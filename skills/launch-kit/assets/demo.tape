# VHS tape template. Render with:  vhs demo.tape
# Docs: https://github.com/charmbracelet/vhs
#
# Use this when the demo must be a GIF or MP4 (interactive programs, or posts
# on X / Reddit / Product Hunt, which do not accept SVG). For a README-only
# demo, scripts/term_demo.py needs no extra tools.

Output assets/demo.gif
# Output assets/demo.mp4        # add a second Output line for video

# Fail early if the tool is not on PATH.
Require mytool

Set Shell "bash"
Set FontSize 22
Set Width 1200
Set Height 600
Set Padding 24
Set TypingSpeed 60ms
Set Theme "GitHub Dark"

# Setup the viewer should not see (cd into sample data, clear the screen).
Hide
Type "cd examples && clear"
Enter
Show

# Scene: one command, its real output, a pause long enough to read it.
Type "mytool scan ."
Sleep 400ms
Enter
Sleep 3s

Type "mytool fix --dry-run"
Sleep 400ms
Enter
Sleep 4s
