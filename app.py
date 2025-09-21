import json
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import streamlit as st


@dataclass
class Player:
    """Represents a player in the Five Dice game."""

    name: str
    scorecard: Dict[str, Optional[int]] = field(
        default_factory=lambda: {
            "ones": None,
            "twos": None,
            "threes": None,
            "fours": None,
            "fives": None,
            "sixes": None,
            "three_of_a_kind": None,
            "four_of_a_kind": None,
            "full_house": None,
            "small_straight": None,
            "large_straight": None,
            "Five Dice": None,
            "chance": None,
        }
    )

    def get_upper_section_total(self) -> int:
        """Calculate upper section total."""
        upper_categories = ["ones", "twos", "threes", "fours", "fives", "sixes"]
        total = sum(score for score in [self.scorecard[cat] for cat in upper_categories] if score is not None)
        return total

    def get_upper_section_bonus(self) -> int:
        """Calculate upper section bonus (35 points if total >= 63)."""
        return 35 if self.get_upper_section_total() >= 63 else 0

    def get_total_score(self) -> int:
        """Calculate total score including bonus."""
        total = sum(score for score in self.scorecard.values() if score is not None)
        return total + self.get_upper_section_bonus()


class FiveDiceGame:
    """Main game logic for Five Dice."""

    def __init__(self):
        self.dice = [1, 1, 1, 1, 1]
        self.previous_dice = [1, 1, 1, 1, 1]  # Track previous roll for animation
        self.dice_held = [False, False, False, False, False]
        self.rolls_left = 3
        self.current_player = 0
        self.players = []
        self.game_over = False
        self.just_rolled = False  # Track if dice were just rolled

    def roll_dice(self) -> None:
        """Roll the dice that aren't held."""
        if self.rolls_left > 0:
            self.previous_dice = self.dice.copy()  # Save previous state
            for i in range(5):
                if not self.dice_held[i]:
                    self.dice[i] = random.randint(1, 6)
            self.rolls_left -= 1
            self.just_rolled = True

    def toggle_die_hold(self, die_index: int) -> None:
        """Toggle whether a die is held."""
        if 0 <= die_index < 5:
            self.dice_held[die_index] = not self.dice_held[die_index]

    def calculate_score(self, category: str, dice: List[int]) -> int:
        """Calculate score for a given category."""
        dice_counts = [dice.count(i) for i in range(1, 7)]
        # Upper section
        if category in ["ones", "twos", "threes", "fours", "fives", "sixes"]:
            value = ["ones", "twos", "threes", "fours", "fives", "sixes"].index(category) + 1
            return dice.count(value) * value
        # Lower section
        elif category == "three_of_a_kind":
            return sum(dice) if max(dice_counts) >= 3 else 0
        elif category == "four_of_a_kind":
            return sum(dice) if max(dice_counts) >= 4 else 0
        elif category == "full_house":
            counts_set = set(dice_counts)
            return 25 if 3 in counts_set and 2 in counts_set else 0
        elif category == "small_straight":
            dice_set = set(dice)
            straights = [{1, 2, 3, 4}, {2, 3, 4, 5}, {3, 4, 5, 6}]
            return 30 if any(straight.issubset(dice_set) for straight in straights) else 0
        elif category == "large_straight":
            dice_set = set(dice)
            return 40 if dice_set in [{1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}] else 0
        elif category == "Five Dice":
            return 50 if max(dice_counts) == 5 else 0
        elif category == "chance":
            return sum(dice)
        return 0

    def score_category(self, category: str) -> bool:
        """Score the current dice roll in the specified category."""
        current_player_obj = self.players[self.current_player]
        if current_player_obj.scorecard[category] is not None:
            return False  # Category already filled
        score = self.calculate_score(category, self.dice)
        current_player_obj.scorecard[category] = score
        # Reset for next turn
        self.dice_held = [False, False, False, False, False]
        self.rolls_left = 3
        self.just_rolled = False  # Reset animation flag
        self.current_player = (self.current_player + 1) % len(self.players)
        # Check if game is over
        if all(all(score is not None for score in player.scorecard.values()) for player in self.players):
            self.game_over = True
        return True

    def get_winner(self) -> Optional[Player]:
        """Get the winner of the game."""
        if not self.game_over:
            return None
        return max(self.players, key=lambda p: p.get_total_score())


# Color palettes for different rolls
COLOR_PALETTES = {
    "Cool": {
        1: "#E3F2FD",  # Light blue
        2: "#BBDEFB",  # Medium blue  
        3: "#90CAF9",  # Darker blue
    },
    "Pastels": {
        1: "#F8BBD9",  # Light pink
        2: "#E1BEE7",  # Light purple
        3: "#C5CAE9",  # Light indigo
    },
    "Warm": {
        1: "#FFECB3",  # Light yellow
        2: "#FFD54F",  # Medium yellow
        3: "#FFA726",  # Orange
    },
    "Hot": {
        1: "#FFCDD2",  # Light red
        2: "#EF5350",  # Medium red
        3: "#D32F2F",  # Dark red
    },
    "Sunny Day": {
        1: "#FFF9C4",  # Very light yellow
        2: "#FFF176",  # Medium yellow
        3: "#FF9800",  # Orange
    }
}


def initialize_game() -> None:
    """Initialize a new game."""
    if "game" not in st.session_state:
        st.session_state.game = FiveDiceGame()
        st.session_state.game.players = [Player("Player 1"), Player("Player 2")]
    
    # Initialize color palette if not set
    if "color_palette" not in st.session_state:
        st.session_state.color_palette = "Cool"


def get_roll_color() -> str:
    """Get the current color based on rolls left."""
    game = st.session_state.game
    palette = COLOR_PALETTES[st.session_state.color_palette]
    
    # Map rolls_left to roll number (3 rolls_left = 1st roll, 2 = 2nd, 1 = 3rd, 0 = finished)
    if game.rolls_left == 3:
        return "#FFFFFF"  # White for initial state
    elif game.rolls_left == 2:
        return palette[1]  # First roll
    elif game.rolls_left == 1:
        return palette[2]  # Second roll
    else:
        return palette[3]  # Third roll


def render_color_palette_selector() -> None:
    """Render color palette selection in sidebar."""
    with st.sidebar:
        st.subheader("🎨 Dice Colors")
        
        selected_palette = st.selectbox(
            "Choose color theme:",
            options=list(COLOR_PALETTES.keys()),
            index=list(COLOR_PALETTES.keys()).index(st.session_state.color_palette),
            key="palette_selector"
        )
        
        if selected_palette != st.session_state.color_palette:
            st.session_state.color_palette = selected_palette
            st.rerun()
        
        # Show color preview
        st.write("**Roll Colors:**")
        palette = COLOR_PALETTES[selected_palette]
        for roll_num, color in palette.items():
            st.markdown(
                f'<div style="background-color: {color}; padding: 8px; margin: 2px 0; border-radius: 4px; text-align: center; border: 1px solid #ccc;">Roll {roll_num}</div>',
                unsafe_allow_html=True
            )


def render_dice() -> None:
    """Render the dice with hold/unhold functionality and color-coded rolls."""
    st.subheader("🎲 Dice")
    game = st.session_state.game
    
    # Show instruction only when rolls have started
    if game.rolls_left < 3:
        st.caption("💡 Tap dice to hold/unhold them")
    
    dice_emoji = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    
    # Get current roll color
    roll_color = get_roll_color()
    
    # Create global CSS that targets buttons based on their position/content
    dice_css = f"""
    <style>
    /* Use a more aggressive approach - target ALL buttons in this section */
    div[data-testid="stVerticalBlock"] button {{
        font-size: 4rem !important;
        width: 100% !important;
        padding: 5px !important;
        line-height: 1 !important;
        font-family: 'Segoe UI Emoji', 'Apple Color Emoji', sans-serif !important;
        border-radius: 20px !important;
        border-width: 4px !important;
        font-weight: normal !important;
        transition: all 0.3s ease !important;
        margin: 0 !important;
    }}

    div[data-testid="stVerticalBlock"] button p {{
        font-size: 1.5rem
    }}
    
    /* Style primary buttons (unheld dice) */
    div[data-testid="stVerticalBlock"] button[data-testid="stBaseButton-primary"] {{
        background-color: {roll_color} !important;
        color: #222222 !important;
        border-color: #aaaaaa !important;
    }}
    
    /* Style secondary buttons (held dice) */  
    div[data-testid="stVerticalBlock"] button[data-testid="stBaseButton-secondary"] {{
        background-color: #444444 !important;
        color: #ffffff !important;
        border-color: #222222 !important;
    }}
    
    /* Hover effects for all buttons */
    div[data-testid="stVerticalBlock"] button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
        border-color: #777777 !important;
    }}
    
    /* Disabled buttons */
    div[data-testid="stVerticalBlock"] button:disabled {{
        opacity: 0.5 !important;
        transform: none !important;
        cursor: not-allowed !important;
    }}
    
    /* Target buttons more specifically by their container */
    .stButton button {{
        background-color: {roll_color} !important;
        color: #222222 !important;
        font-size: 4rem !important;
        border: 4px solid #aaaaaa !important;
        border-radius: 20px !important;
        font-family: 'Segoe UI Emoji', 'Apple Color Emoji', sans-serif !important;
    }}
    
    .stButton button[kind="secondary"] {{
        background-color: #444444 !important;
        color: #ffffff !important;
        border-color: #222222 !important;
    }}
    </style>
    """
    st.markdown(dice_css, unsafe_allow_html=True)
    
    # All 5 dice in one row
    col1, col2, col3, col4, col5 = st.columns(5)
    dice_cols = [col1, col2, col3, col4, col5]
    
    for i, col in enumerate(dice_cols):
        with col:
            die_value = game.dice[i]
            is_held = game.dice_held[i]
            
            # Determine display and button type
            if is_held:
                dice_display = f"🔒{dice_emoji[die_value]}"
                button_type = "secondary"
            else:
                dice_display = dice_emoji[die_value]
                button_type = "primary"
            
            if st.button(
                dice_display,
                key=f"dice_button_{i}",
                disabled=game.rolls_left == 3,
                type=button_type,
                use_container_width=True
            ):
                game.toggle_die_hold(i)
                st.rerun()
    
    # Add dice held display under the dice
    if game.rolls_left < 3:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        
        # Get held dice emoji
        held_dice = [game.dice[i] for i in range(5) if game.dice_held[i]]
        
        if held_dice:
            held_dice_display = "".join([dice_emoji[die] for die in held_dice])
            st.markdown(
                f"""
                <div style='text-align: center; margin: 10px 0;'>
                    <div style='font-weight: bold; font-size: 1.1rem; color: #555; margin-bottom: 5px;'>
                        Dice Held ({len(held_dice)})
                    </div>
                    <div style='font-size: 2rem; letter-spacing: 4px;'>
                        {held_dice_display}
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style='text-align: center; margin: 10px 0;'>
                    <div style='font-weight: bold; font-size: 1.1rem; color: #555; margin-bottom: 5px;'>
                        Dice Held (0)
                    </div>
                    <div style='font-size: 1.2rem; color: #888; font-style: italic;'>
                        None
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )


def render_roll_section() -> None:
    """Render the roll dice section with enhanced visuals."""
    game = st.session_state.game
    current_player = game.players[game.current_player]

    st.subheader(f"🎯 {current_player.name}'s Turn")

    col1, col2 = st.columns([1, 2])  # Removed the third column since dice held moved

    with col1:
        st.metric("Rolls Left", game.rolls_left)

    with col2:
        # Enhanced roll button
        roll_button_disabled = game.rolls_left == 0 or game.game_over

        button_text = "🎲 ROLL DICE" if game.rolls_left > 0 else "🚫 No Rolls Left"

        if st.button(button_text, disabled=roll_button_disabled, type="primary", use_container_width=True):
            game.roll_dice()
            # Show rolling effect
            with st.spinner("🎲 Rolling dice..."):
                time.sleep(0.8)  # Visual delay for effect
            st.rerun()


def render_scoring_section() -> None:
    """Render the scoring section."""
    game = st.session_state.game
    current_player = game.players[game.current_player]
    if game.rolls_left == 3:  # Haven't rolled yet
        st.info("🎲 Roll the dice to see scoring options!")
        return
    st.subheader("📊 Choose Your Score")
    categories = {
        "Upper Section": {
            "ones": "Ones",
            "twos": "Twos",
            "threes": "Threes",
            "fours": "Fours",
            "fives": "Fives",
            "sixes": "Sixes",
        },
        "Lower Section": {
            "three_of_a_kind": "3 of a Kind",
            "four_of_a_kind": "4 of a Kind",
            "full_house": "Full House",
            "small_straight": "Small Straight",
            "large_straight": "Large Straight",
            "Five Dice": "Five Dice",
            "chance": "Chance",
        },
    }
    for section_name, section_categories in categories.items():
        with st.expander(section_name, expanded=True):
            cols = st.columns(2)
            for i, (category, display_name) in enumerate(section_categories.items()):
                col = cols[i % 2]
                with col:
                    # Check if category is already filled
                    if current_player.scorecard[category] is not None:
                        st.button(
                            f"✅ {display_name}: {current_player.scorecard[category]}",
                            disabled=True,
                            key=f"filled_{category}",
                        )
                    else:
                        potential_score = game.calculate_score(category, game.dice)
                        score_button_type = "primary" if potential_score > 0 else "secondary"
                        if st.button(
                            f"{display_name}: {potential_score} pts",
                            key=f"score_{category}",
                            type=score_button_type,
                        ):
                            if game.score_category(category):
                                st.success(f"🎉 Scored {potential_score} points in {display_name}!")
                                st.rerun()


def render_scoreboard() -> None:
    """Render the current scoreboard."""
    st.subheader("🏆 Scoreboard")
    game = st.session_state.game
    # Create scoreboard table
    score_data = []
    categories = [
        ("ones", "Ones"),
        ("twos", "Twos"),
        ("threes", "Threes"),
        ("fours", "Fours"),
        ("fives", "Fives"),
        ("sixes", "Sixes"),
        ("upper_total", "Upper Total"),
        ("upper_bonus", "Upper Bonus"),
        ("three_of_a_kind", "3 of a Kind"),
        ("four_of_a_kind", "4 of a Kind"),
        ("full_house", "Full House"),
        ("small_straight", "Small Straight"),
        ("large_straight", "Large Straight"),
        ("Five Dice", "Five Dice"),
        ("chance", "Chance"),
        ("total", "TOTAL"),
    ]
    for category, display_name in categories:
        row = {"Category": display_name}
        for player in game.players:
            if category == "upper_total":
                row[player.name] = player.get_upper_section_total()
            elif category == "upper_bonus":
                row[player.name] = player.get_upper_section_bonus()
            elif category == "total":
                row[player.name] = player.get_total_score()
            else:
                score = player.scorecard.get(category)
                row[player.name] = score if score is not None else "-"
        score_data.append(row)
    st.dataframe(score_data, use_container_width=True)


def render_game_status() -> None:
    """Render game status."""
    game = st.session_state.game
    if game.game_over:
        winner = game.get_winner()
        st.balloons()  # Celebration effect!
        st.success(f"🎉 Game Over! {winner.name} wins with {winner.get_total_score()} points!")
    else:
        current_player = game.players[game.current_player]
        st.info(f"🎮 Current turn: {current_player.name}")


def render_new_game_button() -> None:
    """Render new game button at the bottom."""
    st.markdown("---")
    st.subheader("🎮 Game Controls")

    # Add some spacing and a warning
    st.warning("⚠️ Starting a new game will reset all progress!")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:  # Center the button
        if st.button("🔄 Start New Game", type="secondary", use_container_width=True):
            # Reset the game
            st.session_state.game = FiveDiceGame()
            st.session_state.game.players = [Player("Player 1"), Player("Player 2")]
            st.success("🎉 New game started!")
            st.rerun()


def main():
    """Main function to run the Dice Game page."""
    st.set_page_config(
        page_title="Dice Game - Five Dice", 
        page_icon="🎲", 
        layout="wide", 
        initial_sidebar_state="expanded"
    )

    # Enhanced CSS for mobile optimization and visual effects
    st.markdown(
        """
    <style>
    .stButton > button {
        width: 100%;
        margin: 2px 0;
        transition: all 0.2s ease;
        border-radius: 8px;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stColumns > div {
        padding: 0 4px;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .stButton > button {
            font-size: 16px;
            padding: 12px 16px;
            min-height: 60px;
        }
        .stColumns > div {
            padding: 0 2px;
        }
    }
    
    /* Remove default button styling for dice */
    [class*="dice-"] button {
        background: none !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Ensure dice buttons maintain their custom styling */
    [class*="dice-"] button:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    
    [class*="dice-"] button:active {
        transform: translateY(-1px) !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("🎲 Five Dice Dice Game")
    st.markdown("*A classic dice game for two players*")

    # Initialize game
    initialize_game()
    
    # Render color palette selector in sidebar
    render_color_palette_selector()

    # Game rules expander
    with st.expander("📋 How to Play", expanded=False):
        st.markdown(
            """
        **Objective:** Score the most points by rolling five dice to make certain combinations.
        
        **Gameplay:**
        1. Each player takes turns rolling 5 dice up to 3 times per turn
        2. After each roll, choose which dice to keep (hold) and which to re-roll
        3. After your rolls, choose a category to score your dice
        4. Each category can only be used once per player
        5. If you can't make a valid combination, you must take a zero in any category
        
        **Dice Colors:**
        - Dice change color with each roll to show your progress
        - Held dice appear darker with a lock icon
        - Customize colors using the sidebar selector
        
        **Scoring Categories:**
        - **Upper Section:** Count and add only dice of the specified number
        - **3/4 of a Kind:** Sum of all dice if you have 3/4 of the same number
        - **Full House:** 25 points for 3 of one number and 2 of another
        - **Small Straight:** 30 points for 4 consecutive numbers
        - **Large Straight:** 40 points for 5 consecutive numbers
        - **Five Dice:** 50 points for 5 of the same number
        - **Chance:** Sum of all dice
        
        **Bonus:** Get 35 extra points if your upper section totals 63 or more!
        """
        )

    # Game status
    render_game_status()

    # Main game layout
    if not st.session_state.game.game_over:
        # Active game layout
        col1, col2 = st.columns([2, 3])
        with col1:
            render_roll_section()
            render_dice()
        with col2:
            render_scoring_section()

    # Always show scoreboard
    render_scoreboard()

    # New game button at the bottom
    render_new_game_button()

    # Footer
    st.markdown("---")
    st.markdown("*🎲 Optimized for mobile play • Two-player Five Dice*")


if __name__ == "__main__":
    main()