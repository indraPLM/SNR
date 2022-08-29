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
layout1 = st.sidebar.columns(2)
with layout1[0]: 
    d0 = st.slider('Waktu Sebelum (menit)', 0, 10, 2)
with layout1[-1]: 
    d1 = st.slider('Waktu Sesudah (menit)', 0, 60, 10)

layout2 = st.sidebar.columns(2)
with layout2[0]: 
    nama_jar = st.text_input('Jaringan Seismik:', 'IA') 
with layout2[-1]: 
    nama_sta = st.text_input('Nama Stasiun:', 'BBJI') 

layout3 = st.sidebar.columns(2)
with layout3[0]: 
    nama_chan = st.selectbox('Channel:',('SHZ','SH*', 'BHZ', 'BH*', 'HHZ','HH*')) 
with layout3[-1]: 
    window = st.slider('Window Spectrum', 0, 60, 20)
    

### ----------------------- Obtaining Waveform & Plotting  ----------------------
st.markdown(
    """
    ### 1. Menampilkan Waveform Seismic
    """)


fdsn_client = Client(client_link,user=client_user,password=client_pass)
eq_time = UTCDateTime(datetime_event)
evt_list=fdsn_client.get_events(starttime=eq_time-10, endtime=eq_time+60,
                                minlatitude=-15,maxlatitude=10,
                                minlongitude=85,maxlongitude=150,
                                mindepth=0,maxdepth=600,
                                minmagnitude=4.0,maxmagnitude=9.5)

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

### ----------------------- Signal To Noise Processing ----------------------

st.markdown(
    """
    ### 3. Menampilkan Signal To Noise Ratio
    """)

# Spectrum Signal
sta_raw=sta.copy()
sta_ori=sta.copy()

from obspy.geodetics import locations2degrees
from obspy.taup import TauPyModel

origin = evt_list[0].preferred_origin()
coords = inv.get_coordinates("%s.%s..%s" %(nama_jar,nama_sta,nama_chan))
distance = locations2degrees(origin.latitude, origin.longitude,
                             coords["latitude"], coords["longitude"])

model = TauPyModel(model="ak135")
arrivals_phase = model.get_travel_times(source_depth_in_km=origin.depth / 1000.0,
                                  distance_in_degree=distance,phase_list=["p", "s"])

#Trimming Gelombang P
sta_sigP=sta.copy()
sig_P=sta_sigP.trim(eq_time+arrivals_phase[0].time,
                   eq_time+arrivals_phase[0].time+window)

#Trimming Gelombang S
sta_sigS=sta.copy()
sig_S=sta_sigS.trim(eq_time+arrivals_phase[1].time,
                   eq_time+arrivals_phase[1].time+window)

#Trimming Gelombang Noise
sta_noise=sta_ori.copy()
sig_N=sta_noise.trim(eq_time+arrivals_phase[0].time-(window+10),
                   eq_time+arrivals_phase[0].time-10)


from multitaper import MTSpec
import multitaper.utils as utils

# MTSPEC parameters
nw    = 4.0
kspec = 7
delta = sig_P[0].stats.delta

# Get MTSPEC class
Py1   = MTSpec(sig_P[0].data,nw,kspec,delta)
Py2   = MTSpec(sig_S[0].data,nw,kspec,delta)
Py3   = MTSpec(sig_N[0].data,nw,kspec,delta)

Pspec = [Py1, Py2, Py3]
# Get positive frequencies
freq ,spec1   = Py1.rspec()
freq ,spec2   = Py2.rspec()
freq ,spec3   = Py3.rspec()

# Get spectral ratio
sratio1 = np.sqrt(spec1/spec3)
sratio2 = np.sqrt(spec2/spec3)

# SNR Value
SNR_P=np.sqrt(spec1).mean()/np.sqrt(spec3).mean()
SNR_S=np.sqrt(spec2).mean()/np.sqrt(spec3).mean()

from matplotlib.gridspec import GridSpec

fig = plt.figure(constrained_layout=True)

gs = GridSpec(3, 2, figure=fig)
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(sta_ori[0].times("matplotlib"), sta_ori[0].data, "k",label='All Sinyal')
ax1.plot(sig_P[0].times("matplotlib"), sig_P[0].data, "r", label='Window Gel.P')
ax1.plot(sig_S[0].times("matplotlib"), sig_S[0].data, "g", label='Window Gel.S')
ax1.plot(sig_N[0].times("matplotlib"), sig_N[0].data, "b", label='Window Noise')
ax1.legend(loc=1,prop={'size':5})
ax1.xaxis_date()

ax2 = fig.add_subplot(gs[-1, 0])
ax2.margins(0.05)           
ax2.loglog(freq,np.sqrt(spec1*window),'r', label='Spectrum Gel.P')
ax2.loglog(freq,np.sqrt(spec3*window),'--',color='b',label='Spectrum Noise')
ax2.set_title('Spectrum Gelombang P \n ## SNR= %6.2f ##' %(SNR_P))
ax2.legend(loc=1,prop={'size':5})
ax2.grid()

ax3 = fig.add_subplot(gs[-1, -1])
ax3.margins(0.05)           
ax3.loglog(freq,np.sqrt(spec2*window),'g',label='Spectrum Gel.S')
ax3.loglog(freq,np.sqrt(spec3*window),'--',color='b',label='Spectrum Noise')
ax3.set_title('Spectrum Gelombang S \n ## SNR= %6.2f ##' %(SNR_S))
ax3.legend(loc=1,prop={'size':5})
ax3.grid()

# identical to ax1 = plt.subplot(gs.new_subplotspec((0, 0), colspan=3))
ax4 = fig.add_subplot(gs[-2, :])
ax4.loglog(freq,np.sqrt(spec1*window),'r',label='Spectrum Gel.P')
ax4.loglog(freq,np.sqrt(spec2*window),'g',label='Spectrum Gel.S')
ax4.loglog(freq,np.sqrt(spec3*window),'--',color='b',label='Spectrum Noise')
ax4.legend(loc=1,prop={'size':5})
ax4.grid()
ax4.set_ylim(1e-10,1e-1)
ax4.set_xlabel('Frequency (Hz)')
ax4.set_ylabel('Amplitude Spectrum')

plt.show()

plt.savefig('signal_to_noise.png')
image = Image.open('signal_to_noise.png')
st.image(image, caption='Processing Sinyal To Noise Ratio')





