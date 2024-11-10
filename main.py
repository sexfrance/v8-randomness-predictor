import z3
import struct
import subprocess
import json
import argparse
from logmagix import *

log = Logger()

def main(custom_sequence=None):
    if custom_sequence:
        sequence = custom_sequence
    else:
        js_code = """
        const sequence = Array(5).fill().map(() => Math.random());
        console.log(JSON.stringify(sequence));
        """
        result = subprocess.run(['node', '-e', js_code], capture_output=True, text=True)
        sequence = json.loads(result.stdout) #! Edit this with a directory if you want to test it manually, it should have at least 5 Math.random() values it can be more. E.g: [0.05202328742387219, 0.30364247635586117, 0.7183273228185958, 0.3068890956782795, 0.6674550856854704]

    sequence = sequence[::-1]

    log.debug(f"Using Sequence: {sequence}" )

    solver = z3.Solver()

    se_state0, se_state1 = z3.BitVecs("se_state0 se_state1", 64)

    for i in range(len(sequence)):
        se_s1 = se_state0
        se_s0 = se_state1
        se_state0 = se_s0
        se_s1 ^= se_s1 << 23
        se_s1 ^= z3.LShR(se_s1, 17)
        se_s1 ^= se_s0
        se_s1 ^= z3.LShR(se_s0, 26)
        se_state1 = se_s1
        float_64 = struct.pack("d", sequence[i] + 1)
        u_long_long_64 = struct.unpack("<Q", float_64)[0]
        mantissa = u_long_long_64 & ((1 << 52) - 1)
        solver.add(int(mantissa) == z3.LShR(se_state0, 12))

    if solver.check() == z3.sat:
        model = solver.model()

        states = {}
        for state in model.decls():
            states[state.__str__()] = model[state]

        log.debug(f"States: {states}")

        state0 = states["se_state0"].as_long()
        u_long_long_64 = (state0 >> 12) | 0x3FF0000000000000
        float_64 = struct.pack("<Q", u_long_long_64)
        next_sequence = struct.unpack("d", float_64)[0]
        next_sequence -= 1

        log.success(f"Successfully guessed result: {next_sequence}")
        input()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V8 Randomness Predictor")
    parser.add_argument("--sequence", type=str, help="Custom sequence as a JSON array")
    args = parser.parse_args()

    custom_sequence = json.loads(args.sequence) if args.sequence else None
    main(custom_sequence)