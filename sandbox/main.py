from lib_imu_20948_horizon_rev01_v08 import *

# gyro_full_scale = 1000
gyro_full_scale = 2000
# gyro_sample_rate = 50
gyro_sample_rate = 100
gyro_low_pass = 3

# accel_full_scale = 2
accel_full_scale = 8
# accel_sample_rate = 50
accel_sample_rate = 100
accel_low_pass = 3

magnetometer_sample_mode = 50

i2c_mst_sample_rate = 275 #все варианты 1100, 550, 275, 137, 70

imu = ICM20948( gfs=gyro_full_scale\
                ,gsr=gyro_sample_rate\
                ,glp=gyro_low_pass\
                ,afs=accel_full_scale\
                ,asr=accel_sample_rate
                ,alp=accel_low_pass\
                ,msm=magnetometer_sample_mode\
                ,isr=i2c_mst_sample_rate)

try:
    while True:
        acc_arr, gyr_arr, mag_arr, temp = imu.read_full_data()

        print("""
Accel: {:05.2f} {:05.2f} {:05.2f}
Gyro:  {:05.2f} {:05.2f} {:05.2f}
Mag:   {:05.2f} {:05.2f} {:05.2f}""".format(
        acc_arr[0], acc_arr[1], acc_arr[2], gyr_arr[0], gyr_arr[1], gyr_arr[2], mag_arr[0], mag_arr[1], mag_arr[2]
    ))

        time.sleep(0.5)
except (KeyboardInterrupt, SystemExit) as exErr:
    imu.powerOff()
    print("\nEnding program")
    sys.exit(0)