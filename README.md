# pop-monitor

```
git clone https://github.com/Mantodkaz/pop-monitor
cd pop-monitor

python3 -m venv venv
source venv/bin/activate

pip3 install -r requirements.txt
python3 monitor.py
```

Modify [Line 29](https://github.com/Mantodkaz/pop-monitor/blob/main/monitor.py#L29) in `monitor.py` to exclude your custom SSH port if it's not 22.
