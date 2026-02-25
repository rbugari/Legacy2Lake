
import bcrypt

hash_to_check = "$2b$12$fWI2kbA1EHUNCgO47Woh5.SMhe5JV4gDKIvU.vlixVLnRxz9KfYFu".encode('utf-8')

candidates = [
    "A2321rfb!", "A2321rfb", "A1111rfb!", "A1111rfb",
    "A2321rfb.", "A1111rfb.", "A2321rfb_", "A1111rfb_",
    "admin123", "Admin123", "Admin123!", "admin123!",
    "UTM2026", "UTM2025", "Legacy2Lake", "L2L2026"
]


print(f"Checking hash: {hash_to_check.decode('utf-8')}")
for password in candidates:
    if bcrypt.checkpw(password.encode('utf-8'), hash_to_check):
        print(f"MATCH FOUND: {password}")
        exit(0)

print("No match found in candidates.")
    
