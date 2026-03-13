"""Default Anki card CSS styles.

Used as fallback when deck.json does not specify css or css_file.
"""

DEFAULT_CSS = """.card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}
.replay-button svg {
 width: 40px;
 height: 40px;
}
.replay-button svg circle {
 fill: #279FF5;
}
.replay-button svg path {
 fill: white;
}
"""

# Noun article colors
COLOR_DER = "#279FF5"  # blue
COLOR_DIE = "#F5279F"  # pink
COLOR_DAS = "#9FF527"  # green
