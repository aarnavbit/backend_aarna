import time
from app.services.game_state import game_state

class ScoreService:
    POINTS_PER_MATCH = 100
    ROUND_BONUS = 150
    MISMATCH_PENALTY = 20
    MAX_SPEED_BONUS = 100

    @classmethod
    def calculate_score(cls, matches: int, mismatches: int, rounds_completed: int, duration_ms: int, is_early_submit: bool = False) -> int:
        base_score = (matches * cls.POINTS_PER_MATCH) + (rounds_completed * cls.ROUND_BONUS)
        penalty = mismatches * cls.MISMATCH_PENALTY
        
        # Simple speed bonus: faster gives more points, up to 100 bonus points max per round completed
        max_bonus = cls.MAX_SPEED_BONUS * max(1, rounds_completed)
        speed_bonus = max(0, max_bonus - ((duration_ms // 1000) * 5))
        
        total = base_score + speed_bonus - penalty
        
        if is_early_submit:
            # Early submit penalty explicitly sent
            total -= 500
        elif rounds_completed >= 5:
            # Global time bonus for finishing the whole game from start to finish
            if duration_ms < 45000:
                total += 3000
            elif duration_ms < 75000:
                total += 1500
            elif duration_ms < 120000:
                total += 500
                
        return max(0, total)

    @classmethod
    def validate_and_score(cls, matches: int, mismatches: int, rounds_completed: int, client_duration_ms: int, is_early_submit: bool = False):
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

        score = cls.calculate_score(matches, mismatches, rounds_completed, client_duration_ms, is_early_submit)
        
        return {
            "score": score,
            "round_ended": round_ended,
            "duration_ms": client_duration_ms
        }
