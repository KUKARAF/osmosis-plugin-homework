from pathlib import Path


HOMEWORK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "request_homework_photo",
            "description": (
                "When the user asks for help with homework, call this tool to prompt them "
                "to photograph their assignment. Do not attempt to help with homework without "
                "first calling this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "The subject of the homework (e.g. English, Spanish, French, Math)",
                    },
                    "message": {
                        "type": "string",
                        "description": "A friendly prompt to show the user, asking them to photograph their homework",
                    },
                },
                "required": ["subject", "message"],
                "additionalProperties": False,
            },
        },
    }
]


class HomeworkPlugin:
    name = "homework"
    version = "0.1.0"

    def get_tools(self) -> list[dict]:
        return HOMEWORK_TOOLS

    def get_tool_handlers(self) -> dict:
        from osmosis_homework.handlers import handle_request_homework_photo
        return {"request_homework_photo": handle_request_homework_photo}

    def get_router(self):
        from osmosis_homework.router import router
        return router

    def get_media_types(self) -> list[str]:
        return ["homework"]

    def get_goal_actions(self) -> list[dict]:
        return []

    def get_prompts_dir(self) -> Path | None:
        return None

    async def on_startup(self, app) -> None:
        pass
