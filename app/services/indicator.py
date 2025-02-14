
import numpy as np
from numba import njit, float64, int64, optional

@njit(float64[:](float64[:], int64), fastmath=True)
def calculate_last_two_sma(arr: np.ndarray, window: int) -> np.ndarray:
    """
    Calculate only the last two Simple Moving Averages using Numba.
    Pre-compiled for float64 arrays and int64 window size.
    """
    n = len(arr)
    result = np.zeros(2, dtype=np.float64)
    if n < window:
        return result
    sum_last = 0.0
    for i in range(n - window, n):
        sum_last += arr[i]
    result[1] = sum_last / window
    if n > window:
        sum_second_last = 0.0
        for i in range(n - window - 1, n - 1):
            sum_second_last += arr[i]
        result[0] = sum_second_last / window
    else:
        result[0] = result[1]

    return result

def calculate_sma(prices, window):
    """
    Calculate the Simple Moving Average (SMA) over the last 'window' prices using Numba.
    """
    np_prices = np.array(prices, dtype=float)
    return calculate_last_two_sma(np_prices, window)


wap_sig = [
    float64(
        float64[:, ::1],  # bids_arr: 2D C-contiguous array of float64
        float64[:, ::1],  # asks_arr: 2D C-contiguous array of float64
        optional(int64)  # levels: optional integer
    )
]
@njit(wap_sig, nopython=True, cache=True)
def calculate_wap(bids_arr, asks_arr, levels=None):
    """
    Numba-optimized WAP calculator for pre-converted numpy arrays.
    
    Args:
        bids_arr: numpy array of shape (N, 2) with float prices and volumes
        asks_arr: numpy array of shape (N, 2) with float prices and volumes
        levels: optional number of levels to consider
    """
    if levels is None:
        levels = len(bids_arr)
    
    total_value = 0.0
    total_volume = 0.0
    
    
    for i in range(min(levels, len(bids_arr))):
        price = bids_arr[i, 0]
        volume = bids_arr[i, 1]
        total_value += price * volume
        total_volume += volume
    
    
    for i in range(min(levels, len(asks_arr))):
        price = asks_arr[i, 0]
        volume = asks_arr[i, 1]
        total_value += price * volume
        total_volume += volume
    
    if total_volume == 0:
        return 0.0
        
    return total_value / total_volume