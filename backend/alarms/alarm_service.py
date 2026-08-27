import asyncio

from backend.actions.action_engine import ActionEngine
from backend.persistence.alarm_repository import AlarmRepository


class AlarmService:
    def __init__(
        self,
        *,
        alarms: AlarmRepository,
        actions: ActionEngine,
        interval: float = 0.25,
    ):
        self.alarms = alarms
        self.actions = actions
        self.interval = interval

    async def run(self) -> None:
        while True:
            due = await asyncio.to_thread(self.alarms.claim_due)
            for alarm in due:
                print("[CYPHER ALARM]", alarm)
                try:
                    result = await asyncio.to_thread(self.actions.alert)
                    print("[CYPHER ALARM ACTION]", result)
                    sound = await asyncio.to_thread(
                        self.actions.play_sound,
                        "ALERT",
                    )
                    print("[CYPHER ALARM SOUND]", sound)

                    if alarm["kind"] == "timer":
                        await asyncio.to_thread(
                            self.alarms.complete,
                            alarm["id"],
                        )
                        reset = await asyncio.to_thread(self.actions.idle)
                        print("[CYPHER TIMER COMPLETE]", reset)
                except Exception as error:
                    print("[CYPHER ALARM ACTION ERROR]", error)
            await asyncio.sleep(self.interval)
