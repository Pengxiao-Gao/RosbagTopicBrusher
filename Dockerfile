FROM memory_cruise_brush:base

WORKDIR /root/memory_cruise_brush
COPY . .

ENTRYPOINT ["/root/memory_cruise_brush/entrypoint.sh", "python3.7", "memory_cruise_refresh.py"]