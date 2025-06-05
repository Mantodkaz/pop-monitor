#!/bin/bash

total_cores=$(nproc)
core_index=0

for irq in $(ls /proc/irq | grep -E '^[0-9]+$'); do
    irq_path="/proc/irq/$irq"
    affinity_file="$irq_path/smp_affinity"

    irq_desc=$(grep "^ *$irq:" /proc/interrupts | awk '{$1=""; print $0}')
    
    if [[ "$irq_desc" =~ (virtio|eth|enp|ens|eno) ]]; then

        total_interrupts=$(grep "^ *$irq:" /proc/interrupts | awk '{for(i=2;i<=NF-3;i++)sum+=$i}END{print sum+0}')
        if [[ "$total_interrupts" -eq 0 ]]; then
            continue
        fi

        core=$(( core_index % total_cores ))
        mask=$((1 << core))
        hexmask=$(printf "%x" "$mask")

        echo "[*] IRQ $irq ($irq_desc) -> core $core (mask 0x$hexmask)"
        if echo "$hexmask" > "$affinity_file" 2>/dev/null; then
            echo "Success"
        else
            echo "Failed (permission or locked by hypervisor)"
        fi

        ((core_index++))
    fi
done

echo "[*] IRQ pinning completed."
