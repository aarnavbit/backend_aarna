import time
from app.services.game_state import game_state

class ScoreService:
    POINTS_PER_MATCH = 10
    ROUND_BONUS = 50
    MISMATCH_PENALTY = 5

    @classmethod
    def calculate_score(cls, matches: int, mismatches: int, rounds_completed: int, duration_ms: int) -> int:
        base_score = (matches * cls.POINTS_PER_MATCH) + (rounds_completed * cls.ROUND_BONUS)
        penalty = mismatches * cls.MISMATCH_PENALTY
        
        # Simple speed bonus: faster gives more points, up to 100 bonus points max
        speed_bonus = max(0, 100 - (duration_ms // 1000))
        
        total = base_score + speed_bonus - penalty
        return max(0, total)

    @classmethod
    def validate_and_score(cls, matches: int, mismatches: int, rounds_completed: int, client_duration_ms: int):
        state = game_state.get_state()
        
        if state["status"] == 'waiting':
            raise ValueError("Game is not active")

        # Anti-headstart / server time validation
        now_ms = int(time.time() * 1000)
        
        if not state["start_time"]:
            raise ValueError("Game start time not found")
            
        elapsed_ms = now_ms - state["start_time"]
        
        # Allow a small buffer for network latency (e.g., 2000ms)
        if client_duration_ms > elapsed_ms + 2000:
            raise ValueError("Invalid duration: client duration exceeds elapsed server time.")
            
        # Physical human plausibility: min 600ms per round
        if client_duration_ms < (rounds_completed * 600):
            raise ValueError("Invalid duration: physically impossible completion time.")

        # Late submission enforcement
        round_ended = state["status"] == 'ended'

        score = cls.calculate_score(matches, mismatches, rounds_completed, client_duration_ms)
        
        return {
            "score": score,
            "round_ended": round_ended,
            "duration_ms": client_duration_ms
        }
