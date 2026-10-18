"""Belief Through Time Short cover (drawn fallback and final lettering): the first 1.7 s of every Short is a designed thumbnail frame.
Same lettering as the long thumbnails (cover_text.py: Cinzel cream-gold capitals, ornament rules, brand mark) on the Short's first scene."""
from cover_text import cover as _c

def cover(frame, title, n, path, ep=0):
    _c(frame, title, path)

if __name__ == "__main__":
    import sys; cover(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4])
