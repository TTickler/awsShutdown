from difflib import SequenceMatcher


string1 = "ncct-bsim"
string2 = "ncc-bsim"

m = SequenceMatcher(None, string1, string2)
print(m.ratio())