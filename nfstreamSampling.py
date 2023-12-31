from nfstream import NFStreamer
import pandas as pd
import argparse
import numpy as np
from datetime import datetime

def Sampling(cap):
    stream = NFStreamer(source=cap, accounting_mode=3, statistical_analysis=True)
    info = stream.to_pandas()[["id", "requested_server_name", "src_ip", "dst_ip", "src_port", "dst_port", "protocol", "src2dst_bytes"
                               , "dst2src_bytes","bidirectional_first_seen_ms", "bidirectional_last_seen_ms",
                               "bidirectional_duration_ms","bidirectional_packets", "bidirectional_bytes", "bidirectional_max_piat_ms", 
                               "bidirectional_mean_piat_ms","bidirectional_min_piat_ms",
                               "bidirectional_rst_packets", "bidirectional_fin_packets", "bidirectional_psh_packets"]]
    
    return info

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', nargs='?',required=True, help='input file')
    parser.add_argument('-w', '--window', nargs='?',required=False, help='samplig delta interval (sec)',default=1)
    parser.add_argument('-d', '--decision', nargs='?',required=False, help='decision',default=0)
    parser.add_argument('-s', '--sni', nargs='?',required=False, help='API SNI',default="")
    args = parser.parse_args()

    deltams = float(args.window)*1000
    sni = args.sni
    slide = float(args.decision)*1000
    output_file = ''.join(args.input.split('.')[:-1])+"_features.dat"
    output_file = 'features/'+output_file
    data = Sampling('caps/'+args.input)

    data = data.sort_values(by=['bidirectional_first_seen_ms'])

    win = np.where(data['bidirectional_first_seen_ms'] < 1694013408122)

    if sni != "":
        data = data[data['requested_server_name'] == sni]
    
    Ti = data.iloc[0]['bidirectional_first_seen_ms']
    Tf = data.iloc[-1]['bidirectional_first_seen_ms']
    print("First timestamp: {} - {}".format(Ti,datetime.utcfromtimestamp(Ti/1000)))
    print("Last timestamp: {} - {}".format(Tf,datetime.utcfromtimestamp(Tf/1000)))

    t = Ti
    obs = 0
    while t < Tf-deltams:
        cond1 = data['bidirectional_first_seen_ms'] > t
        cond2 = data['bidirectional_first_seen_ms'] < t+deltams
        win = np.where(cond1&cond2)
        
        nflows = data.iloc[win]['id'].count()

        avgdownbytes = data.iloc[win]['dst2src_bytes'].mean()
        stddownbytes = data.iloc[win]['dst2src_bytes'].std()
        maxdownbytes = data.iloc[win]['dst2src_bytes'].max()
        mindownbytes = data.iloc[win]['dst2src_bytes'].min()

        avgupbytes = data.iloc[win]['src2dst_bytes'].mean()
        stdupbytes = data.iloc[win]['src2dst_bytes'].std()
        maxupbytes = data.iloc[win]['src2dst_bytes'].max()
        minupbytes = data.iloc[win]['src2dst_bytes'].min()

        avgduration = (data.iloc[win]['bidirectional_last_seen_ms']-data.iloc[win]['bidirectional_first_seen_ms']).mean()
        stdduration = (data.iloc[win]['bidirectional_last_seen_ms']-data.iloc[win]['bidirectional_first_seen_ms']).std()
        minduration = (data.iloc[win]['bidirectional_last_seen_ms']-data.iloc[win]['bidirectional_first_seen_ms']).min()
        maxduration = (data.iloc[win]['bidirectional_last_seen_ms']-data.iloc[win]['bidirectional_first_seen_ms']).max()

        avgratio = (data.iloc[win]['dst2src_bytes']/data.iloc[win]['src2dst_bytes']).mean()
        stdratio = (data.iloc[win]['dst2src_bytes']/data.iloc[win]['src2dst_bytes']).std()
        minratio = (data.iloc[win]['dst2src_bytes']/data.iloc[win]['src2dst_bytes']).min()
        maxratio = (data.iloc[win]['dst2src_bytes']/data.iloc[win]['src2dst_bytes']).max()

        avgpackets = data.iloc[win]["bidirectional_packets"].mean()
        stdpackets = data.iloc[win]["bidirectional_packets"].std()
        maxpackets = data.iloc[win]["bidirectional_packets"].max()
        minpackets = data.iloc[win]["bidirectional_packets"].min()


        maxmaxpiat = data.iloc[win]["bidirectional_max_piat_ms"].max()
        minminpiat = data.iloc[win]["bidirectional_min_piat_ms"].min()

        
        silence = []
        for idx in range(len(data.iloc[win])):
            if data.iloc[idx+1]["bidirectional_first_seen_ms"] and data.iloc[idx]["bidirectional_last_seen_ms"]:
                silence.append(data.iloc[idx+1]["bidirectional_first_seen_ms"] - data.iloc[idx]["bidirectional_last_seen_ms"])

        avgsilence = np.mean(silence)
        stdsilence = np.std(silence)
        maxsilence = np.max(silence)
        minsilence = np.min(silence)

        avgpiat = data.iloc[win]["bidirectional_mean_piat_ms"].mean()
        stdpiat = data.iloc[win]["bidirectional_mean_piat_ms"].std()

        t += slide
        obs += 1

        if nflows > 0:
            f = np.nan_to_num(np.array([nflows, avgduration, stdduration, minduration, maxduration, 
                                        avgpackets, stdpackets, minpackets, maxpackets, avgdownbytes, stddownbytes, mindownbytes, maxdownbytes,
                                        avgupbytes, stdupbytes, minupbytes, maxupbytes, avgpiat, stdpiat, minminpiat, maxmaxpiat,
                                        avgsilence, stdsilence, minsilence, maxsilence, avgratio, stdratio, minratio, maxratio]))
            print(f)
            if 'allfeatures' not in locals():
                    allfeatures = f.copy()
            else:
                    allfeatures = np.vstack((allfeatures, f))

    np.savetxt(output_file, allfeatures, fmt='%.4f')
    
    


if __name__ == '__main__':
    main()