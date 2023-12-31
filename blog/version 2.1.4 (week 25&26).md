
# week 26

We finished in 2nd last reset, incredible performance.



## Issues 

* Week 24/25 (node W) - sent the starting probe to the wrong waypoint, so couldn't buy and more probes. The conductor was having market monitoring override shipyard monitoring tasks.
* The DB container didn't have ship_mounts table populated because that came from the `reset_db.py` script that we're not using.   Changed to materialized view - fixed node V and C's conductors from failing.
* Command ship W--1 drifting for chain trades. 
* Performance of UI / DB is attrocious