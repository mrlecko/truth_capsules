# Makefile deltas to patch


-e TZ=UTC -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 -e PYTHONHASHSEED=0 -e HOME=/tmp -e PYTHONPYCACHEPREFIX=/tmp/__pycache__
--ulimit nofile=256:256 --ulimit core=0 --stop-timeout=5
ENV file support (in addition to ENV_VARS):

bash
Copy code
# If ENV_FILE is set, prefer it
ENVOPT=""; [ -n "$(ENV_FILE)" ] && ENVOPT="--env-file $(ENV_FILE)";
...
"$$ENGINE" run $(SANDBOX_FLAGS) $$ENVOPT \
  -v "$$(pwd)":/work:ro \
  "$${EV_ARR[@]}" \
  --entrypoint /bin/sh "$$IMG" -lc "$$CMD";
Mount scope (optional mode):

bash
Copy code
# Example narrow mounts:
-v "$$(pwd)/scripts:/work/scripts:ro" \
-v "$$(pwd)/capsules:/work/capsules:ro" \
-v "$$(pwd)/artifacts:/work/artifacts:ro"