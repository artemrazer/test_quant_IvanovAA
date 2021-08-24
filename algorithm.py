import csv

with open('tmp.csv', newline='') as File:
    reader = list(csv.reader(File))

# print(reader[0])

# ''' Order book visualization '''
# for i in range(20):
#     if i < 10:
#         print('ask', reader[1][14-i], reader[1][24-i])
#     else:
#         print('bid', reader[1][25-10+i], reader[1][35-10+i])

print('enter child order size (1000 / 10 000/ 1 000 000)')
c_order_size = int(input())
if c_order_size == 1000:
    change_ld_time = 57000000
    buy_any_time = 57000000
elif c_order_size == 10000:
    change_ld_time = 45000000
    buy_any_time = 57000000
    nv_i = 2
elif c_order_size == 1000000:
    change_ld_time = 65000000
    buy_any_time = 65000000
    nv_i = 10
    # nv_i_small = 6
else:
    print('invalid child order size')
    exit()

data = [['id', 'time(utc timestamp)', 'amount(USD)', 'price', 'side']]
trade_id, trade_id_sl, average_slippage = 0, 0, 0
side = 'buy'
time_threshold = int(reader[1][3])
trade = False


''' this function executes a market order if the order placed for sale at the lowest price 
    is insufficient to satisfy our volume. '''


def multi_trade_execute():
    global average_slippage, trade_id, trade_id_sl, trade

    volume_left = float(c_order_size)
    i, mean_trade_price, amount_bought = 0, 0, 0
    average_slippage -= float(ob_data[5])

    while volume_left > 0:
        if float(ob_data[15 + i]) <= volume_left:
            volume_left -= float(ob_data[15 + i])
            data.append([str(trade_id), ob_data[3], ob_data[15 + i], ob_data[5 + i], side])
            mean_trade_price += float(ob_data[15 + i])
            amount_bought += float(ob_data[15 + i]) / float(ob_data[5 + i])
            i += 1
            trade_id += 1
        else:
            data.append([str(trade_id), ob_data[3], str(volume_left), ob_data[5 + i], side])
            trade_id += 1
            trade_id_sl += 1
            mean_trade_price += volume_left
            amount_bought += volume_left / float(ob_data[5 + i])
            volume_left = 0
            trade = True
    mean_trade_price = mean_trade_price / amount_bought
    average_slippage += mean_trade_price


''' The order book monitoring algorithm is as follows. 
    Every minute, we first search for a volume at the minimum price sufficient to satisfy our order. 
    Upon reaching a certain point in time, if the deal has not yet been executed, the search range expands; 
    we begin to look "deeper" in the order book. 
    If this volume remains insufficient, at the end of the minute the order is executed at any available prices. '''

for ob_data in reader[1:]:

    if not trade and int(ob_data[3]) - time_threshold < change_ld_time:
        if (c_order_size == 1000 or c_order_size == 10000) and float(ob_data[15]) >= c_order_size:
            data.append([str(trade_id), ob_data[3], str(c_order_size), ob_data[5], side])
            trade_id += 1
            trade_id_sl += 1
            trade = True
        elif c_order_size == 1000000:
            nearest_values_sum = sum([float(ob_data[k]) for k in range(15, 15 + nv_i)])
            if nearest_values_sum >= c_order_size:
                multi_trade_execute()

    elif not trade and int(ob_data[3]) - time_threshold < buy_any_time:
        if c_order_size == 10000:
            nearest_values_sum = sum([float(ob_data[k]) for k in range(15, 15 + nv_i)])
            if nearest_values_sum >= c_order_size:
                multi_trade_execute()
        # elif c_order_size == 1000000:
        #     nearest_values_sum = sum([float(ob_data[k]) for k in range(15, 15 + nv_i_big)])
        #     if nearest_values_sum >= c_order_size:
        #         multi_trade_execute()

    elif not trade and int(ob_data[3]) - time_threshold > buy_any_time:
        multi_trade_execute()

    if int(ob_data[3]) - time_threshold >= 60000000:
        trade = False
        time_threshold += 60000000

total_amount_bought, average_price = 0, 0

print(data[0])
for row in data[1:]:
    print(row)
    total_amount_bought += float(row[2]) / float(row[3])
    average_price += float(row[2])

''' write .csv-file with trades data '''
# myFile = open('trades.csv', 'w', newline='')
# with myFile:
#     writer = csv.writer(myFile)
#     writer.writerows(data)

average_price = average_price / total_amount_bought

print('amount of purchased instrument:', round(total_amount_bought, 8))
print('average purchase price:', round(average_price, 2))
print('average slippage:', round(average_slippage / trade_id_sl, 2))
