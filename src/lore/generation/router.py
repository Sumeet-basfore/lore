"""Multi-model LLM Router supporting local Ollama, cloud APIs, and mock test mode."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from lore.core.exceptions import LLMRouteError
from lore.core.models import ContentAtom, LoreConfig, Platform
from lore.intelligence.angle_finder import StoryAngle


class LLMRouter:
    """Dispatches prompt completions to Ollama or configured cloud LLM providers."""

    def __init__(self, config: Optional[LoreConfig] = None):
        from lore.config import load_config
        self.config = config or load_config()
        self._init_templates()

    def _init_templates(self) -> None:
        templates_dir = Path(__file__).parent / "prompts"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_prompt(
        self,
        platform: Platform,
        project_name: str,
        atom: ContentAtom,
        tech_stack: Optional[list] = None,
        angle: Optional[StoryAngle] = None,
        voice_context: Optional[str] = None,
    ) -> str:
        """Renders the appropriate Jinja2 template for the target platform."""
        template_name = f"{platform.value}.j2"
        try:
            template = self.jinja_env.get_template(template_name)
        except Exception as e:
            raise LLMRouteError(f"Template not found for platform {platform}: {e}") from e

        return template.render(
            project_name=project_name,
            atom=atom,
            tech_stack=tech_stack or atom.tech_stack,
            angle=angle,
            voice_context=voice_context,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        force_mock: bool = False,
    ) -> str:
        """Executes LLM generation through the configured provider."""
        active_provider = (provider or self.config.llm_provider).lower()
        active_model = model or self.config.llm_model

        if force_mock or os.environ.get("LORE_MOCK_LLM") == "1":
            return self._mock_completion(prompt)

        if active_provider == "ollama":
            return self._complete_ollama(prompt, system_prompt, active_model, temperature)
        elif active_provider == "openai":
            return self._complete_openai(prompt, system_prompt, active_model, temperature)
        elif active_provider == "anthropic":
            return self._complete_anthropic(prompt, system_prompt, active_model, temperature)
        elif active_provider in ["openrouter", "gemini"]:
            return self._complete_openai_compatible(
                prompt, system_prompt, active_provider, active_model, temperature
            )
        else:
            raise LLMRouteError(f"Unsupported LLM provider: {active_provider}")

    def _complete_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
    ) -> str:
        """Calls local Ollama HTTP API."""
        base_url = self.config.ollama_base_url.rstrip("/")
        url = f"{base_url}/api/chat"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            with httpx.Client(timeout=90.0) as client:
                res = client.post(url, json=payload)
                if res.status_code != 200:
                    raise LLMRouteError(f"Ollama error ({res.status_code}): {res.text}")
                data = res.json()
                return data.get("message", {}).get("content", "").strip()
        except httpx.ConnectError:
            # If Ollama is not currently running, provide informative error
            raise LLMRouteError(
                f"Could not connect to Ollama at {base_url}. Ensure Ollama is running (`ollama serve`)."
            )
        except Exception as e:
            raise LLMRouteError(f"Ollama generation failed: {e}") from e

    def _complete_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
    ) -> str:
        api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMRouteError("OPENAI_API_KEY is not configured.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": model, "messages": messages, "temperature": temperature}

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    raise LLMRouteError(f"OpenAI error ({res.status_code}): {res.text}")
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise LLMRouteError(f"OpenAI request failed: {e}") from e

    def _complete_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
    ) -> str:
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMRouteError("ANTHROPIC_API_KEY is not configured.")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 2048,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    raise LLMRouteError(f"Anthropic error ({res.status_code}): {res.text}")
                data = res.json()
                return data["content"][0]["text"].strip()
        except Exception as e:
            raise LLMRouteError(f"Anthropic request failed: {e}") from e

    def _complete_openai_compatible(
        self,
        prompt: str,
        system_prompt: Optional[str],
        provider: str,
        model: str,
        temperature: float,
    ) -> str:
        if provider == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
            api_key = self.config.api_key or os.environ.get("OPENROUTER_API_KEY")
        else:
            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            api_key = self.config.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")

        if not api_key:
            raise LLMRouteError(f"API key for {provider} is not configured.")

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": model, "messages": messages, "temperature": temperature}

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    raise LLMRouteError(f"{provider} API error ({res.status_code}): {res.text}")
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise LLMRouteError(f"{provider} request failed: {e}") from e

    def _mock_completion(self, prompt: str) -> str:
        """Deterministic mock completion for testing and offline simulations."""
        if "Twitter/X post" in prompt:
            return "Shipped real-time sync in Python today. Swapped polling for WebSockets across 4 files, cutting background request overhead to near zero."
        elif "Twitter thread" in prompt:
            return (
                "We just moved our live sync from polling to WebSockets.\n---\n"
                "The issue: polling was hitting our database 50 times a second per active tab.\n---\n"
                "The fix: 350 lines of Python using a lightweight pub/sub channel in Redis.\n---\n"
                "Result: latency dropped from 2s to 40ms. If you are polling in 2026, consider switching."
            )
        elif "LinkedIn" in prompt:
            return (
                "Today we replaced our database polling loop with a direct WebSocket sync.\n\n"
                "When we first built the sync layer, polling was simple and got us to production fast. "
                "At small volume it worked fine. But as active connections grew, the query load grew with it.\n\n"
                "We refactored the pipeline into an event-driven channel over WebSockets. "
                "Total footprint: 350 lines added, 4 files touched, zero new external framework dependencies.\n\n"
                "The takeaway: start with the simplest thing that works, but keep your transport layer decoupled so refactoring is painless."
            )
        else:
            return "# Technical Update\n\nShipped real-time sync layer with WebSockets and Redis pub/sub."
