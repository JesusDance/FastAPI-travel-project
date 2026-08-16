import json

import openai
from fastapi import HTTPException, status
from google.genai import Client
from openai import AsyncOpenAI

from app.api.dependencies import Settings
from app.schemas.ai import Suggestions


class AiClient:
    def __init__(self, client: Client | AsyncOpenAI, settings: Settings):
        self.client = client
        self.settings = settings


    @staticmethod
    async def _get_prompt(
            existing_places: list[str],
            project_name: str,
            project_description: str | None,
            days: int,
            preferences: str | None,
    ):
        return f"""
                You are a travel recommendation assistant.
                Suggest additional places to visit based on the travel project.

                Project name:
                {project_name}

                Project description:
                {project_description or "Not provided"}

                Place already added:
                {", ".join(existing_places) or "No places added yet"}

                Days:
                {days}

                Preferences:
                {preferences or "Preferences not provided"}

                Do not recommend places already listed.
                Return only valid JSON in this format:
                {{ 
                    "project_name": "{project_name}",
                    "suggestions": [
                    {{
                        "name": "Place name",
                        "category": "museum",
                        "reason": "Why this place is recommended",
                        "estimated_visit_minutes": 90
                    }}
                    ]
                }}
                """


    async def get_suggestions_openai(
            self,
            existing_places: list[str],
            project_name: str,
            project_description: str | None,
            days: int,
            preferences: str | None,
    ) -> Suggestions:
        prompt = await self._get_prompt(
            existing_places, project_name, project_description, days, preferences
        )

        try:
            response = await self.client.responses.parse(
                model=self.settings.OPENAI_MODEL,
                input=prompt,
                text_format=Suggestions,
            )
            return response.output_parsed
        except openai.RateLimitError:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "You exceeded your current quota, "
                "please check your plan and billing details."
            )


    async def get_suggestions_gemini(
            self,
            existing_places: list[str],
            project_name: str,
            project_description: str | None,
            days: int,
            preferences: str | None,
    ) -> Suggestions:
        prompt = await self._get_prompt(
            existing_places, project_name, project_description, days, preferences
        )

        response = await self.client.aio.models.generate_content(
            model=self.settings.GEMINI_MODEL,
            contents=prompt,
        )
        response_json = json.loads(response.text)
        return Suggestions.model_validate(response_json)

