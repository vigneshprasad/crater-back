# Creator Tokens Architecture

This is the complete flow of the Creator coins **buying/selling, auctioning, bidding and transactions** that happen
on the platform.

Model breakdown goes as follows.

### Creator

This is a user who is hosting content on the platform. Creators can do livestreams on the platform and create communities.

### Coins

This is a **currency of a particular creator** on the platform, in exchange for which the creator can offer rewards to
his community members/followers.

### Auctions

Creator can create an **auction for their coins** (for price discovery of various rewards) and then his community members
can bid on the coins for certain price.

- Auction A is open to be bid on. A total of 100 coins are being auction by Creator C.
  - Should we create a Transaction when a creator does auction for 100 coins? From Crater to Creator C.
  - How will we track how much coins the Creator C has in the market? At start do we own all the coins?
- User A comes in and wants to buy X coins at a Y price.
- Bid gets placed for User A at Y/X price per coin, Y amount is put on hold from User A's card.
- User B bid for Z coins at W price.
- Above step is repeated and a bid object is created and certain amount is held from users bank account.
- Higher bid gets accepted and the payment hold is processed towards Crater and other user's payment is rejected.
- In this case assume User B is the highest bidder. He gets Z coins from the creator. Payment is completed for User B.
- A transaction object is created for User B and Creator C, with the number of coins (Z coins).
- User B coin holding is created with the number of coins (Z) from the creator.
- User B can redeem these coins for 1:1, AMA, group calls from Creator C.


### Backed Architecture (Table states)

The modular structure in the backend will look something like the following:

We have opened an auction from a Creator C.

**Auction**:
```
coin - Creator C coin
number of coins - 100
creator - Creator C
```

**State 1**: Bid is made for coins, payment is held.

Bid is placed by User A and User B, for Creator C's coins.

**Bid**:

```
bidder - User A
coin -  Creator C coin
number of coins - X coins
price of coin - Y/X (per coin)
status - Pending
```
----
```
bidder -  User B
coin -  Creator C coin
number of coins - Z coins
price of coin - W/Z (per coin)
status - Pending
```

**Payment**:
```
user - User A
price - Y
status - On Hold
```
---
```
user - User B
price - W
status - On Hold
```

**State Two**: Bid acceptance and rejection states.

In this case User B's bid gets accepted and User A's bid for the coins gets rejected.

**Bid:**
```
bidder - User A
coin -  Creator C coin
number of coins - X coins
price of coin - Y/X (per coin)
status - Rejected
```
----
```
bidder -  User B
coin -  Creator C coin
number of coins - Z coins
price of coin - W/Z (per coin)
status - Accepted
```

**Payment:**
```
user - User A
price - Y
status - Rejected
```
---
```
user - User B
price - W
status - Success
```

**Transaction:**

**Note:** No transaction is created for User A, since the bid was rejected and no actual coins were
moved through the market.

```
buyer - User B
seller - Creator C
number of coins - Z
price - Z
type - Creator to User
```

**UserCoinHolding:**
```
user - User B
coin - Creator C coin
number of coins - Z
```

**State 3:** The User B redeems a reward after buying Creator C's coins.

**Reward:**
```
name - 1:1 with Creator C
number of coins - 10
```

**Redemption:**
```
user - User B
reward - Above reward.
```

**Transaction:**

In this case the Creator earns back the coins they auctioned before, they can auction the coins again.

**Note:** Is this right?

```
buyer - Creator C
seller - User B
number of coins - 10
type - User to Creator
```

**UserCoinHolding:**
```
user - User B
coin - Creator C coin
number of coins - (-10) coins -  used for redeeming the rewards.
```
