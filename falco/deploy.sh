docker run -it \
           --name falco \
           --privileged \
           -v /sys/kernel/tracing:/sys/kernel/tracing:ro \
           -v /var/run/docker.sock:/host/var/run/docker.sock \
           -v /proc:/host/proc:ro \
           -v /etc:/host/etc:ro \
           -v $(pwd)/custom_rules.yaml:/etc/falco/falco_rules.local.yaml \
           -v $(pwd)/falco.yaml:/etc/falco/falco.yaml \
           falcosecurity/falco