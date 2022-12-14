# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 06:38:59 2022

@author: Asus
"""
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
from obspy.signal.trigger import classic_sta_lta,recursive_sta_lta,plot_trigger,trigger_onset
from PIL import Image


st.set_page_config(page_title='SNR Processing',  layout='centered', page_icon="🌍")
st.title('SNR Processing Seismic Waveform')

st.sidebar.header("Parameter Inputs :")
client_link=st.sidebar.text_input('Network Link', 'IRIS')
layout = st.sidebar.columns(2)
with layout[0]:
    client_user=st.text_input('User', )
with layout[-1]: 
    client_pass=st.text_input('Password',value="", type="password" )
    
datetime_event=st.sidebar.text_input('Waktu Gempa:', '2019-08-02T12:03:25')
layout = st.sidebar.columns(2)
with layout[0]: 
    d0 = st.slider('Waktu Sebelum (menit)', 0.0, 10.0, 2.0)
with layout[-1]: 
    d1 = st.slider('Waktu Sesudah (menit)', 0.0, 60.0, 10.0)

layout1 = st.sidebar.columns([2, 1])
with layout1[0]: 
    nama_jar = st.text_input('Jaringan Seismik:', 'IA') 
with layout1[-1]: 
    nama_sta = st.text_input('Nama Stasiun:', 'BBJI') 

layout2 = st.sidebar.columns(2)
with layout2[0]: 
    nama_chan = st.selectbox('Channel:',('SHZ','SH*', 'BHZ', 'BH*', 'HHZ','HH*')) 
with layout2[-1]: 
    window = st.slider('Window Spectrum', 0, 60, 20)

### ----------------------- Obtaining Waveform & Plotting  ----------------------
st.markdown(
    """
    ### 1. Menampilkan Waveform Seismic
    """)


fdsn_client = Client(client_link,user=client_user,password=client_pass)
eq_time = UTCDateTime(datetime_event)

sta = fdsn_client.get_waveforms(network="%s" %(nama_jar), station="%s" %(nama_sta),location='', 
                               channel="%s" %(nama_chan), starttime=eq_time-(d0*60), endtime=eq_time+(d1*60),
                               attach_response=True)

inv=fdsn_client.get_stations(network="%s" %(nama_jar), station="%s" %(nama_sta),location='', 
                               channel="%s" %(nama_chan), starttime=eq_time-(d0*60), endtime=eq_time+(d1*60),
                               level="response")

st.pyplot(sta.plot())

### -----------------------Removing Instrument Processing ----------------------
st.markdown(
    """
    ### 2. Menampilkan Removing Instrument Waveform Sinyal
    """)

if nama_chan=='SH*' or nama_chan=='SHZ':
    pre_filt=(0.005, 0.006, 15.0, 20.0)
if nama_chan=='BH*' or nama_chan=='BHZ':
    pre_filt=(0.005, 0.006, 8.0, 10.0)
if nama_chan=='HH*' or nama_chan=='HHZ':
    pre_filt=(0.005, 0.006, 45, 50.0)

sta.remove_response(output='VEL', pre_filt=pre_filt)
sta.detrend('linear')
sta.detrend('demean')
sta.plot()
st.pyplot(sta.plot())

### -----------------------STA/LTA Trigger Processing ----------------------
st.markdown(
    """
    ### 3. Menampilkan Trigger STA/LTA Sinyal Gempabumi
    """)
df = sta[0].stats.sampling_rate

cft = recursive_sta_lta(sta[0].data, int(10 * df), int(30. * df))
on_of = trigger_onset(cft, 2.5, 0.5)

# Plotting the results
ax = plt.subplot(211)
plt.plot(sta[0].data, 'k')
ymin, ymax = ax.get_ylim()
plt.vlines(on_of[:, 0], ymin, ymax, color='r', linewidth=2)
plt.vlines(on_of[:, 1], ymin, ymax, color='b', linewidth=2)
plt.subplot(212, sharex=ax)
plt.plot(cft, 'k')
plt.hlines([3.5, 0.5], 0, len(cft), color=['r', 'b'], linestyle='--')
plt.axis('tight')
plt.savefig('plot_trigger.png')

image = Image.open('plot_trigger.png')
st.image(image, caption='Trigger STA/LTA')

### ----------------------- Signal To Noise Processing ----------------------

st.markdown(
    """
    ### 4. Menampilkan Signal To Noise Ratio
    """)


# Spectrum Signal
sta_ori = fdsn_client.get_waveforms(network="%s" %(nama_jar), station="%s" %(nama_sta),location='', 
                               channel="%s" %(nama_chan), starttime=eq_time-(d0*60), endtime=eq_time+(d1*60),
                               attach_response=True)


sta_p = fdsn_client.get_waveforms(network="%s" %(nama_jar), station="%s" %(nama_sta),location='', 
                               channel="%s" %(nama_chan), starttime=eq_time-(d0*60), endtime=eq_time+(d1*60),
                               attach_response=True)

t0=sta_p[0].stats.starttime
sta_sig=sta_p.trim(t0+(on_of[0][0]/df),t0+(on_of[0][0]/df)+window)

sta_n = fdsn_client.get_waveforms(network="%s" %(nama_jar), station="%s" %(nama_sta),location='', 
                               channel="%s" %(nama_chan), starttime=eq_time-(d0*60), endtime=eq_time+(d1*60),
                               attach_response=True)

t0=sta_n[0].stats.starttime
sta_noise=sta_n.trim(t0+(on_of[0][0]/df)-(window+10),t0+(on_of[0][0]/df)-10)


from multitaper import MTSpec
import multitaper.utils as utils

# MTSPEC parameters
nw    = 4.0
kspec = 7
delta = sta_sig[0].stats.delta

# Get MTSPEC class
Py1   = MTSpec(sta_sig[0].data,nw,kspec,delta)
Py2   = MTSpec(sta_noise[0].data,nw,kspec,delta)

Pspec = [Py1, Py2]
# Get positive frequencies
freq ,spec1   = Py1.rspec()
freq ,spec2   = Py2.rspec()

# Get spectral ratio
sratio1 = np.sqrt(spec1/spec2)

# SNR Value
SNR_P=np.sqrt(spec1).mean()/np.sqrt(spec2).mean()

from matplotlib.gridspec import GridSpec

fig, axs = plt.subplots(2)
fig.suptitle('Signal To Noise Ratio (SNR) Processing')
plt.subplots_adjust(top = 0.9, bottom=0.09, hspace=0.6, wspace=0.4)
axs[0].plot(sta_ori[0].times("matplotlib"), sta_ori[0].data, "k",label='All Sinyal')
axs[0].plot(sta_sig[0].times("matplotlib"), sta_sig[0].data, "r", label='Window Gel.P')
axs[0].plot(sta_noise[0].times("matplotlib"), sta_noise[0].data, "b", label='Window Noise')
axs[0].legend(loc=1,prop={'size':5})
axs[0].xaxis_date()

axs[1].loglog(freq,np.sqrt(spec1*window),'r', label='Spectrum Gel.P')
axs[1].loglog(freq,np.sqrt(spec2*window),'--',color='b',label='Spectrum Noise')
axs[1].set_title('Spectrum Gelombang P \n ## SNR= %6.2f ##' %(SNR_P))
axs[1].set_xlabel('Frequency (Hz)')
axs[1].set_ylabel('Amplitude Spectrum')
axs[1].set_xlim(0.1,0.95*(df/2))
axs[1].set_ylim(10**0,10**6)
axs[1].legend(loc=1,prop={'size':5})
axs[1].grid()

plt.show()

plt.savefig('signal_to_noise_sta-lta.png')
image = Image.open('signal_to_noise_sta-lta.png')
st.image(image, caption='Processing Sinyal To Noise Ratio')








