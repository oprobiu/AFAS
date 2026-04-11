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
.sentence {
 margin-top: 0.8em;
 padding-top: 0.6em;
 border-top: 1px solid #e0e0e0;
 font-size: 0.9em;
 font-style: italic;
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
hr.sent-sep {
 border: none;
 border-top: 1px dashed #ccc;
 width: 60%;
 margin: 4px auto;
}
"""

# Noun article colors
COLOR_DER = "#279FF5"  # blue
COLOR_DIE = "#F5279F"  # pink
COLOR_DAS = "#9FF527"  # green
