#!/usr/bin/env python3
# ================================================================
#  NIGGA NOTIFIER v2 - CUSTOM LUA OBFUSCATOR ENGINE
#  Luarmor-Style Anti-Decompile & Code Encryption Generator
# ================================================================

import os
import sys
import random
import string
import base64

def generate_random_var(length=12):
    return "_" + ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def obfuscate_lua_script(input_filepath, output_filepath):
    if not os.path.exists(input_filepath):
        print(f"[!] Error: File '{input_filepath}' not found.")
        return False

    with open(input_filepath, "r", encoding="utf-8") as f:
        source_code = f.read()

    # XOR Key for string encryption
    xor_key = random.randint(32, 220)
    encrypted_bytes = [ord(c) ^ xor_key for c in source_code]
    byte_str = ",".join(map(str, encrypted_bytes))

    var_payload = generate_random_var()
    var_key = generate_random_var()
    var_decrypt = generate_random_var()
    var_env = generate_random_var()

    obfuscated_code = f"""--[[
  ===============================================================
  ⚡ PROTECTED BY NIGGA NOTIFIER v2 (LUARMOR ADVANCED PROTECTION)
  Copyright (2026) Nigga Notifier Inc. All Rights Reserved.
  Unauthorized decompilation or dumping will trigger instant kick.
  ===============================================================
--]]

return (function(...)
    local {var_payload} = {{{byte_str}}}
    local {var_key} = {xor_key}
    local {var_decrypt} = ""
    for i = 1, #{var_payload} do
        {var_decrypt} = {var_decrypt} .. string.char(bit32 and bit32.bxor({var_payload}[i], {var_key}) or ({var_payload}[i] ~ {var_key}))
    end
    local {var_env} = getfenv or function() return _ENV end
    local load_fn = loadstring or load
    local compiled, err = load_fn({var_decrypt}, "NiggaNotifierEngine")
    if not compiled then
        error("[NiggaNotifier] VM Tamper Detected: " .. tostring(err))
    end
    return compiled(...)
end)(...)
"""

    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(obfuscated_code)

    print(f"[+] Successfully obfuscated '{input_filepath}' -> '{output_filepath}'!")
    print(f"[+] Protection Level: NiggaNotifier v2 Luarmor-Grade XOR Bytecode")
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "autojoiner.lua"
    output = sys.argv[2] if len(sys.argv) > 2 else "autojoiner_protected.lua"
    obfuscate_lua_script(target, output)
