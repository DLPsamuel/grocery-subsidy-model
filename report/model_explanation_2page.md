## Modeling

We ask how two grocery subsidy policies change consumer welfare in Bronx Community District 2 (CD2). The first is a fixed-cost subsidy to an existing store, either a rent subsidy or a FRESH-style property-tax break. The second is the NYC Groceries contract, under which a store sells core basket items at 30% off. The model is static: shoppers re-choose stores after a policy, but competing stores do not respond.

**Consumers and stores.** Households are grouped by census tract $t$, the finest level with usable data, and by income group $g$ (low, mid, high), because both price sensitivity and grocery spending depend on income. Each consumer group $i = (t, g)$ has $n_i$ households. The choice set $J$ contains the nine existing CD2 grocery stores (six supermarkets and three small independents), plus the planned NYC Groceries store when the contract is modeled.

**Utility.** A group's preference for a store is measured by utility, which ranks stores but has no units of its own. Systematic utility is

$$V_{ij} = \alpha_j + \gamma_{sq}\,(sq_j/1000) - \beta_{p,i}\, b_i\,(p_j - \bar p) - \beta_d\, d_{ij} \qquad (1)$$

where $sq_j$ is floor area, $d_{ij}$ is the street-grid (Manhattan) distance in miles from the tract to the store, $p_j$ is the store's price for a standard basket, and $\bar p$ is the average basket price across stores. A household chooses a store once per trip but buys several baskets on that trip, so the price gap is multiplied by baskets per trip, $b_i = 52\,\bar f_g/(T\,\bar p)$. Here $\bar f_g$ is weekly food-at-home spending and $T = 52$ is trips per year, so $\beta_{p,i}$ is the utility of one dollar of spending per trip. The store-type constant $\alpha_j$ (supermarket or small independent) absorbs what size, price and distance miss, such as variety and quality. $\gamma_{sq}$ and $\beta_d$ come from Hillier et al. (2017); $\alpha_j$ and $\beta_{p,i}$ are calibrated as described below.

**Choice.** Shoppers also respond to factors we do not observe, so total utility is $U_{ij} = V_{ij} + \varepsilon_{ij}$. We assume each $\varepsilon_{ij}$ is an independent draw from a Type I extreme value (Gumbel) distribution, which gives the multinomial logit choice probabilities in closed form (McFadden 1974; Train 2009). Households also shop at bodegas and at stores outside CD2. We group these as an outside option, "other stores" ($j = 0$), with $V_{i0} = 0$. The probability that group $i$ chooses store $j$ is

$$s_{ij} = \frac{\exp(V_{ij})}{1 + \sum_{k \in J} \exp(V_{ik})} \qquad (2)$$

The 1 is the outside option's $e^0$, so the remainder $1 - \sum_j s_{ij}$ is group $i$'s share of trips to other stores.

**Welfare.** Under the same Gumbel assumption, the expected utility of a group's best option on a trip is the "logsum"

$$E\big[\max_k U_{ik}\big] = \ln\Big(1 + \sum_{k \in J} \exp(V_{ik})\Big) + \gamma \qquad (3)$$

where $\gamma \approx 0.577$ is Euler's constant, the mean of the Gumbel distribution, which cancels when changes are taken. Dividing by $\beta_{p,i}$, the utility of a dollar, converts utility to dollars per trip, and multiplying by $T$ makes it annual (Small and Rosen 1981). The annual change in consumer surplus is

$$\Delta CS = \sum_i \frac{n_i\,T}{\beta_{p,i}} \left[\ln\Big(1 + \sum_k e^{V_{ik}^{\text{post}}}\Big) - \ln\Big(1 + \sum_k e^{V_{ik}^{\text{pre}}}\Big)\right] \qquad (4)$$

It counts both savings at a household's usual store and gains from switching stores.

**Policies.** Each policy lowers the basket price at store $j$. We recompute (1) at the new price and evaluate (4). A *rent subsidy or tax break* of $s$ dollars per year lowers the store's fixed costs. A share $\theta$ is passed on to shoppers, spread over the baskets the store sells in a year:

$$\Delta p_j = \theta\, s / \hat Q_j \qquad (5)$$

where $\hat Q_j$ is the model's predicted number of baskets sold at $j$ per year before the policy. At $\theta = 1$, shoppers receive the whole subsidy as lower prices. A fixed-cost subsidy need not change a profit-maximizing store's prices (Weyl and Fabinger 2013), so no published value of $\theta$ applies, and we test $\theta \in \{0.25, 0.50, 0.75\}$.

Under the *NYC Groceries contract*, core items are 30% off, so group $g$'s basket price falls by

$$\Delta p_{j,g} = 0.30\,\kappa_g\,p_j \qquad (6)$$

where $\kappa_g$ is the share of group $g$'s grocery spending that goes to core items; the contract guarantees full pass-through ($\theta = 1$). The city pays the store's rent and property tax, plus an Affordability Payment $AP_j$ if the discount costs more. The store's core share is its core sales over its total sales after shoppers re-sort:

$$\kappa_j = \frac{\sum_i n_i\, s_{ij}^{\text{post}}\, b_i\, \kappa_g}{\sum_i n_i\, s_{ij}^{\text{post}}\, b_i} \qquad (7)$$

Each group's sales at $j$ are $n_i T s_{ij} b_i p_j$; $T$ and the shelf price $p_j$ are the same for every group, so they cancel. The annual public cost of the contract is

$$C_j = \text{Rent}_j + \text{Tax}_j + AP_j = \max\big(\text{Rent}_j + \text{Tax}_j,\; 0.30\,\kappa_j\,\hat R_j^{\text{post}}\big) \qquad (8)$$

where $\hat R_j^{\text{post}}$ is the store's predicted post-policy sales at pre-discount shelf prices. Because a logit model credits any new store with welfare simply for existing, for the planned store we count only the gain from the discount, $\Delta CS(30\%) - \Delta CS(0\%)$.

**Objective.** The decision variable is the subsidy $s$: the rent or tax payment, or for the contract the cost $C_j$ as the discount varies from 0% to 30%. Given a welfare target $\Delta CS_{\min}$ set by the policymaker, we solve

$$s_j^* = \min\{\, s \in [0, \bar s_j] : \Delta CS_j(s) \ge \Delta CS_{\min} \,\} \qquad (9)$$

The cap $\bar s_j$ is the store's rent, its tax bill, or the cost of the full 30% discount; targets beyond it are reported as unreachable. We compare $s_j^*$ across stores and policies for targets from \$50,000 to \$1 million per year.
