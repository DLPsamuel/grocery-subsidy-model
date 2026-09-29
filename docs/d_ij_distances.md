# Distance from Each Income Group to Each Store (d_ij)

Owner: Rahul · Appendix F row: d_ij · Last updated: 2026-09-29

**Files**
- Code: [`code/build_d_ij.py`](../code/build_d_ij.py)
- Output: [`data/distance/d_ij_cd2.csv`](../data/distance/d_ij_cd2.csv) (one distance per income group and store, in miles)
- Detail: [`data/distance/d_tract_store_miles.csv`](../data/distance/d_tract_store_miles.csv) (distance from each of the 16 census tracts to each store)

## Results

Distance in miles is what goes into the model. Minutes are only shown to make the numbers easier to picture.

| Store | Low (mi) | Low (min) | Middle (mi) | Middle (min) | High (mi) | High (min) |
|---|---|---|---|---|---|---|
| Fine Fare (950 Westchester Ave) | 0.48 | 11.6 | 0.54 | 13.0 | 0.55 | 13.3 |
| C-Town (809 Southern Blvd) | 0.55 | 13.3 | 0.51 | 12.4 | 0.54 | 12.9 |
| Antillana (1025 Westchester Ave) | 0.55 | 13.3 | 0.61 | 14.7 | 0.62 | 15.1 |
| Food Fair (1065 E 163rd St) | 0.56 | 13.5 | 0.54 | 13.1 | 0.58 | 13.9 |
| JJ Southern Farm (1046 Southern Blvd) | 0.59 | 14.1 | 0.63 | 15.2 | 0.65 | 15.6 |
| Key Food (1050 Westchester Ave) | 0.63 | 15.1 | 0.68 | 16.4 | 0.69 | 16.7 |
| Sagal (1091 Southern Blvd) | 0.65 | 15.6 | 0.71 | 17.2 | 0.73 | 17.6 |
| Food Universe (724 Hunts Point Ave) | 0.83 | 20.1 | 0.72 | 17.4 | 0.75 | 18.1 |
| C-Town (564 Southern Blvd) | 0.97 | 23.3 | 0.93 | 22.5 | 0.89 | 21.6 |

Income groups: Low = under $25K, Middle = $25K–50K, High = over $50K (household income).
Minutes = walking at the Level 1 spec's 15 min per km (about 24 min per mile).

## How it was calculated

1. **Where people live.** CD2 is split into 16 census tracts (small neighborhood areas). Each tract is represented by its center point.
2. **Distance from each tract to each store.** We use Manhattan distance: the east-west gap plus the north-south gap, the way you'd walk around city blocks instead of cutting straight through them. That's 16 tracts × 9 stores = 144 distances.
3. **One distance per income group.** For each income group, we average the 16 tract distances, giving more weight to tracts where more families of that group live.
   - Example: if most low-income families live in tracts close to Fine Fare, low-income families get a short distance to Fine Fare.
   - Formula: d_ij = Σ_t (households of group i in tract t × distance from tract t to store j) ÷ total households of group i
4. **Result:** 3 income groups × 9 stores = 27 distances, in miles.

Converting latitude and longitude to miles: 1° of latitude = 69.17 miles. 1° of longitude = 69.17 × cos(latitude) miles, about 52.4 miles in the Bronx. At this small scale we treat the ground as flat.

## Data sources

| What | Where it comes from | File |
|---|---|---|
| CD2 census tracts (16) and their center points | NYC Open Data, [2020 Census Tracts](https://data.cityofnewyork.us/City-Government/2020-Census-Tracts/63ge-mke6/about_data). A tract is kept if its center falls inside CD2. | `data/geography/bronx_cd2_tract_centroids.csv` |
| CD2 boundary | NYC Open Data, [Community Districts](https://data.cityofnewyork.us/City-Government/Community-Districts/5crt-au7u) (BoroCD = 202) | `data/geography/bronx_cd2_boundary.geojson` |
| Households by income group in each tract | U.S. Census Bureau, ACS 5-Year 2024, Table B19001 ([Census API](https://www.census.gov/data/developers/data-sets.html)). 19,922 households: 7,683 low, 4,795 middle, 7,444 high. | `data/acs/cd2_B19001_2024.csv` |
| Store locations (latitude and longitude) | NY State Dept. of Agriculture & Markets, [Retail Food Stores](https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj), filtered by hand to the team's final 9 stores | `data/stores/large_grocery_stores_cd2.csv` |
| Method (Manhattan distance, weighted by income group) | Team Datasets sheet, row 18 note | — |

## Caveats

1. **Miles, not minutes.** The Level 1 spec measures d_ij in minutes. We use miles to match the distance papers (Hillier et al. 2017 reports its distance coefficient per mile). The distance sensitivity (β_d) must also be per mile, or the model will be off.
2. **Food Universe uses the old address** (724 Hunts Point Ave). ReferenceUSA lists it at 1334 Louis Nine Blvd, which is just outside CD2, and the team is still deciding. If we switch, rerun `build_d_ij.py` with the new location.
3. **Tract centers are an approximation.** Everyone in a tract is treated as living at its center point. Real distances vary by family.
4. **Manhattan distance assumes streets run north-south and east-west.** Many Bronx streets run at an angle, and some routes are blocked by highways or rail lines (for example the Bruckner Expressway), so real walking routes can be longer.
5. **Income groups end up with similar distances.** Most gaps are under 0.1 mile, because the different income groups live mixed together across the tracts. This means differences in how the groups choose stores will come mostly from their sensitivity numbers (β_d, β_p), not from distance.
6. **Three tracts have no households** (probably the Hunts Point market and industrial area). They get zero weight automatically.
