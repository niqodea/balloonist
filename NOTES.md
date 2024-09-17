# Notes


## A first approach

* Expose balloon specialist, and perhaps even namespace manager with methods
* Create a wrapper method for a factory that takes an existing factory and wraps the objects above in a way such that the domain of balloons is extended with balloons from a new database
  * These balloons can refer to other balloons inside the new database as well as balloons in the wrapped domain


## Problems

* If the wrapper can have same name instances, it can cause the `.get(name)` result to change over time, potentially leading to inconsistent states.
* If the wrapper blocks same name instances, tracking stuff with the wrapped can lead to same names anyways

So we block same name instances and have the wrapped be a factory of providers only (read-only). You cannot wrap a factory of trackers (read-write).

But we currently have no way to have a factory of trackers only. Let's see if it can be implemented easily.

(in all this, we should probably change `BalloonistFactory` to `DatabaseManager`)
