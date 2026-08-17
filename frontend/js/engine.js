/**
 * Game Logic Engine (Pure Logic - Zero DOM dependencies)
 * Handles card generation, shuffling, matching rules, and scoring calculations.
 */
class GameEngine {
  constructor(config) {
    this.config = config || (typeof GameConfig !== 'undefined' ? GameConfig : {});
  }

  // Fisher-Yates Modern Shuffle
  shuffle(array) {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  // Generate shuffled deck of cards for a round
  generateRoundDeck(roundNumber, imagePool, pairsCount = 3) {
    const defaultPool = [
      { img: "images/cards/card_1.webp", name: "Card 1" },
      { img: "images/cards/card_2.webp", name: "Card 2" },
      { img: "images/cards/card_3.webp", name: "Card 3" },
      { img: "images/cards/card_4.webp", name: "Card 4" },
      { img: "images/cards/card_5.webp", name: "Card 5" },
      { img: "images/cards/meme1.webp", name: "Meme 1" },
      { img: "images/cards/meme2.webp", name: "Meme 2" },
      { img: "images/cards/meme3.webp", name: "Meme 3" },
      { img: "images/cards/meme4.webp", name: "Meme 4" }
    ];
    const pool = (Array.isArray(imagePool) && imagePool.length >= pairsCount)
      ? imagePool
      : defaultPool;

    // Pick fresh cards per round so players see new cards each stage
    const startIndex = ((roundNumber - 1) * pairsCount) % pool.length;
    let selectedItems = [];
    for (let i = 0; i < pairsCount; i++) {
      selectedItems.push(pool[(startIndex + i) % pool.length]);
    }

    // Create duplicate pairs with unique card IDs
    const deck = [];
    selectedItems.forEach((item, index) => {
      deck.push({
        id: `r${roundNumber}_p${index}_a`,
        pairId: index,
        content: item,
        isFlipped: false,
        isMatched: false
      });
      deck.push({
        id: `r${roundNumber}_p${index}_b`,
        pairId: index,
        content: item,
        isFlipped: false,
        isMatched: false
      });
    });

    // Shuffle cards thoroughly
    return this.shuffle(deck);
  }

  // Evaluate card tap
  handleCardTap(cardId, state) {
    if (state.isLocked) return null;

    const card = state.cards.find(c => c.id === cardId);
    if (!card || card.isFlipped || card.isMatched) return null;

    // Check currently flipped cards count
    if (state.flippedCardIds.length === 0) {
      state.flipCard(cardId);
      return {
        type: 'first_card_flipped',
        cardId
      };
    } else if (state.flippedCardIds.length === 1) {
      const firstCardId = state.flippedCardIds[0];
      if (firstCardId === cardId) return null; // Can't tap same card twice

      const firstCard = state.cards.find(c => c.id === firstCardId);
      state.flipCard(cardId);

      const isMatch = firstCard.pairId === card.pairId;
      const scoring = this.config.scoring || {
        pointsPerMatch: 100,
        wrongMatchPenalty: 20,
        roundBonus: 150
      };

      if (isMatch) {
        // Points calculation with streak multiplier
        const streakBonus = Math.min(state.streak * 20, 100);
        const pointsEarned = scoring.pointsPerMatch + streakBonus;

        state.setMatched(firstCardId, cardId, pointsEarned);

        const isRoundComplete = state.matchesThisRound >= (this.config.pairsPerRound || 3);

        return {
          type: 'match',
          cardId1: firstCardId,
          cardId2: cardId,
          pointsEarned,
          streak: state.streak,
          isRoundComplete
        };
      } else {
        // Mismatch logic
        const penalty = scoring.wrongMatchPenalty || 20;
        state.isLocked = true;
        state.setMismatch(firstCardId, cardId, penalty);

        return {
          type: 'mismatch',
          cardId1: firstCardId,
          cardId2: cardId,
          penalty,
          delayMs: this.config.mismatchDelayMs || 800
        };
      }
    }

    return null;
  }

  // Calculate speed bonus for completing a round
  calculateRoundBonus(durationMs) {
    const scoring = this.config.scoring || {
      roundBonus: 150,
      maxSpeedBonusPerRound: 100,
      targetRoundDurationSeconds: 10
    };

    const roundBonus = scoring.roundBonus || 150;
    const targetMs = (scoring.targetRoundDurationSeconds || 10) * 1000;

    let speedBonus = 0;
    if (durationMs < targetMs) {
      const ratio = (targetMs - durationMs) / targetMs;
      speedBonus = Math.round(ratio * (scoring.maxSpeedBonusPerRound || 100));
    }

    return {
      roundBonus,
      speedBonus,
      totalBonus: roundBonus + speedBonus
    };
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = GameEngine;
}
