"""Synthetic AcmeDesk support history used to seed Hindsight.
AcmeDesk is a fictional remote-desktop product. All data is synthetic.
"""
from datetime import datetime, timezone

def d(y,m,day,hour=10): return datetime(y,m,day,hour,0,tzinfo=timezone.utc)

CUSTOMERS={
 "priya-sharma":{"name":"Priya Sharma","plan":"Business"},
 "rahul-verma":{"name":"Rahul Verma","plan":"Team"},
 "ananya-iyer":{"name":"Ananya Iyer","plan":"Business"},
 "karthik-reddy":{"name":"Karthik Reddy","plan":"Starter"},
}
TICKETS={
 "priya-sharma":[
  {"when":d(2026,3,4),"issue":"Connection drops roughly every 20 minutes during remote sessions on AcmeDesk 4.2.1.","tried":"Reinstalling AcmeDesk","result":"Not resolved - the drops continued after the reinstall","notes":"Customer was frustrated: this was the third agent she had to explain the issue to. Uses a Windows 11 laptop on home broadband."},
  {"when":d(2026,3,11),"issue":"Connection still dropping every ~20 minutes on AcmeDesk 4.2.1.","tried":"Changed the network configuration profile to Relay mode and restarted AcmeDesk","result":"Resolved - connection stayed stable for weeks","notes":"Customer was relieved and asked us to remember this fix for next time."},
  {"when":d(2026,5,6),"issue":"Connection drops came back after updating to AcmeDesk 4.3.0.","tried":"Repeated the Relay-mode network configuration change and restarted AcmeDesk","result":"Resolved - stable again","notes":"Customer updated to 4.3.0 in late April. Auto-update is turned off on her laptop, so she updates manually."},
 ],
 "rahul-verma":[
  {"when":d(2026,4,14),"issue":"File transfers of large design exports (about 2 GB) stall at 99%.","tried":"Restarting AcmeDesk and retrying the transfer","result":"Not resolved - stalled at 99% again","notes":"High frustration: he has a client deadline. Technical user, prefers short answers without basic steps."},
  {"when":d(2026,4,15),"issue":"Large file transfers still stalling at 99%.","tried":"Turned off transfer compression in the transfer settings","result":"Resolved - the 2 GB export completed","notes":"Customer confirmed transfers have been fine since."},
 ],
 "ananya-iyer":[
  {"when":d(2026,6,2),"issue":"Screen sharing is laggy on a dual 4K monitor setup.","tried":"Lowering the shared screen resolution","result":"Not resolved - still laggy","notes":"Customer presents to clients daily and dislikes lower quality output."},
  {"when":d(2026,6,3),"issue":"Screen sharing lag on dual 4K monitors continues.","tried":"Turned off hardware acceleration and restarted AcmeDesk","result":"Resolved - smooth screen sharing","notes":"Customer was happy that resolution did not have to be reduced."},
 ],
 "karthik-reddy":[
  {"when":d(2026,7,10),"issue":"License activation error AD-4102 after replacing his laptop.","tried":"Reinstalling AcmeDesk and activating again","result":"Not resolved - the same error AD-4102 appeared","notes":"Starter plan customer, new to the product."},
  {"when":d(2026,7,11),"issue":"License activation error AD-4102 on the new laptop.","tried":"Deactivated the old laptop from the account portal, then activated the new one","result":"Resolved - activation succeeded","notes":"Customer wanted plain-language instructions."},
 ]
}
PLAYBOOK=[
 {"when":d(2026,3,20),"issue":"Connection drops about every 20 minutes during remote sessions on AcmeDesk 4.2.x.","tried":"Reinstalling AcmeDesk","result":"Not resolved","notes":"Seen in 4 cases. Reinstalling never fixed it."},
 {"when":d(2026,3,25),"issue":"Connection drops about every 20 minutes during remote sessions on AcmeDesk 4.2.x.","tried":"Changing the network configuration profile to Relay mode and restarting AcmeDesk","result":"Resolved","notes":"Worked in 5 of 5 cases on 4.2.x."},
 {"when":d(2026,6,18),"issue":"Connection drops on AcmeDesk 4.3.0, including after the Relay-mode network configuration change had worked earlier.","tried":"Updating AcmeDesk to 4.3.2 (hotfix for a session keep-alive bug in 4.3.0) and restarting","result":"Resolved","notes":"Resolved 3 of 3 cases. Customers with auto-update turned off stayed on 4.3.0 and kept hitting the drops."},
 {"when":d(2026,7,2),"issue":"Connection drops on AcmeDesk 4.3.0 after the Relay-mode fix stopped holding.","tried":"Repeating the Relay-mode network configuration change and restarting again","result":"Not resolved","notes":"Did not help in 2 cases. Repeating the same fix on 4.3.0 is a dead end."},
 {"when":d(2026,8,5),"issue":"Connection drops continue even on AcmeDesk 4.3.2.","tried":"Escalated to engineering together with the diagnostics bundle","result":"Resolved","notes":"Only 1 case so far, and it needed engineering."},
 {"when":d(2026,4,20),"issue":"Large file transfers stall at 99%.","tried":"Restarting AcmeDesk and retrying","result":"Not resolved","notes":"Seen in 3 cases."},
 {"when":d(2026,4,22),"issue":"Large file transfers stall at 99%.","tried":"Turning off transfer compression in the transfer settings","result":"Resolved","notes":"Worked in 4 of 4 cases."},
 {"when":d(2026,6,10),"issue":"Screen sharing is laggy on multi-monitor or 4K setups.","tried":"Turning off hardware acceleration and restarting AcmeDesk","result":"Resolved","notes":"Worked in 6 of 7 cases. Lowering the shared resolution did not help."},
 {"when":d(2026,7,15),"issue":"License activation error AD-4102 after moving to a new device.","tried":"Deactivating the old device from the account portal, then activating the new one","result":"Resolved","notes":"Worked in 9 of 9 cases. Reinstalling never fixed it."},
]
DEMO_SCENARIOS=[
 {"label":"1) Priya: the fix that worked before fails now","customer":"priya-sharma","message":"My AcmeDesk connection is dropping again. I already changed the network configuration and restarted AcmeDesk like last time, but it is still dropping."},
 {"label":"2) Rahul: recurring file-transfer stall","customer":"rahul-verma","message":"The file transfer is stuck at 99% again on a big export."},
 {"label":"3) New customer, same symptom (playbook only)","customer":"__new__","new_name":"Meera Nair","message":"My AcmeDesk connection keeps dropping every 20 minutes or so."},
]
