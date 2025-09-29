#!/usr/bin/python3
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##   ______   _    _    _____   __ _    _   _  ____                       ##
##  |__  / | | |  / \  / _ \ \ / // \  | \ | |/ ___|                      ##
##    / /| |_| | / _ \| | | \ V // _ \ |  \| | |  _                       ##
##   / /_|  _  |/ ___ \ |_| || |/ ___ \| |\  | |_| |                      ##
##  /____|_| |_/_/___\_\___/_|_/_/_  \_\_| \_\____|                      ##
##  |  _ \  / \  / ___|| | | | | | | / \  |_ _|                           ##
##  | | | |/ _ \ \___ \| |_| | | | |/ _ \  | |                            ##
##  | |_| / ___ \ ___) |  _  | |_| / ___ \ | |                            ##
##  |____/_/   \_\____/|_| |_|\___/_/   \_\___|                           ##
##                                                                            ##
##----------------------------------------------------------------------------##
## zhaoyang                   ## <mzymuzhaoyang@gmail.com>   ##              ##
## dashuai                    ## <dschen2018@gmail.com>      ##              ##
##                            ##                             ##              ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Profile mapping validation and consistency checking utilities.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

import copy
import multiprocessing as mp

import fc.builtin.profiles as btp
import fc.archive as ac
import fc.standards as s
import fc.backend.mapper as mapper


def flatten_mapping(m):
    if isinstance(m, tuple):
        if len(m) == 1:
            m = m[0]
        else:
            m = ",".join([str(x) for x in m])
    return str(m)


def check_profiles():
    errors = []
    summaries = []
    for pname, P in btp.PROFILES.items():
        profile_errors = []
        try:
            A = ac.FCArchive(mp.Queue(), fc_version="CHECK", profile=cp.deepcopy(P))
        except Exception as e:
            profile_errors.append(f"FCArchive init error: {e}")
            errors.append((pname, profile_errors))
            continue

        L = A[ac.fanArray][ac.FA_layers]
        R = A[ac.fanArray][ac.FA_rows]
        C = A[ac.fanArray][ac.FA_columns]
        maxFans = A[ac.maxFans]

        # Per-slave mapping checks
        for idx, S in enumerate(A[ac.savedSlaves]):
            name = S.get(ac.SV_name, f"Slave{idx}")
            rows = S[ac.MD_rows]
            cols = S[ac.MD_columns]
            mapping = flatten_mapping(S[ac.MD_mapping])
            cells = mapping.split(",") if mapping else []
            expected = rows * cols
            if len(cells) != expected:
                profile_errors.append(
                    f"[{name}] cells {len(cells)} != rows*cols {expected} (rows={rows}, cols={cols})"
                )
            for ci, cell in enumerate(cells):
                if cell == "":
                    continue
                parts = cell.split("-")
                if len(parts) > L:
                    profile_errors.append(
                        f"[{name}] cell[{ci}] uses {len(parts)} layers > fanArray.layers {L}"
                    )
                for p in parts:
                    if p == "":
                        continue
                    try:
                        fan_idx = int(p)
                    except Exception:
                        profile_errors.append(f"[{name}] cell[{ci}] bad fan index '{p}'")
                        continue
                    if not (0 <= fan_idx < maxFans):
                        profile_errors.append(
                            f"[{name}] cell[{ci}] fan index {fan_idx} out of range [0, {maxFans})"
                        )

        # Build and validate KG/GK
        try:
            M = Mapper(A)
        except Exception as e:
            profile_errors.append(f"Mapper build error: {e}")
            errors.append((pname, profile_errors))
            continue

        size_k = M.getSize_K()
        size_g = M.getSize_G()

        # Validate bi-directional consistency
        for k in range(size_k):
            g = M.index_KG(k)
            if g == std.PAD:
                continue
            if not (0 <= g < size_g):
                profile_errors.append(
                    f"KG[{k}] -> g={g} out of range (size_g={size_g})"
                )
            else:
                k2 = M.index_GK(g)
                if k2 != k:
                    profile_errors.append(
                        f"KG/GK mismatch: k {k} -> g {g} -> k {k2}"
                    )

        for g in range(size_g):
            k = M.index_GK(g)
            if k == std.PAD:
                continue
            if not (0 <= k < size_k):
                profile_errors.append(
                    f"GK[{g}] -> k={k} out of range (size_k={size_k})"
                )
            else:
                g2 = M.index_KG(k)
                if g2 != g:
                    profile_errors.append(
                        f"GK/KG mismatch: g {g} -> k {k} -> g {g2}"
                    )

        if profile_errors:
            errors.append((pname, profile_errors))
        else:
            summaries.append(pname)

    return errors, summaries


def main():
    errors, ok = check_profiles()
    if ok:
        print("PASS:", ", ".join(ok))
    if errors:
        for pname, plist in errors:
            print(f"\n[Profile: {pname}] FAIL:")
            for e in plist:
                print(" -", e)
        raise SystemExit(1)


if __name__ == "__main__":
    main()