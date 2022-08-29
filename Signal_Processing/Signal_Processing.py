# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 12:02:47 2022

@author: Asus
"""

import streamlit as st
from PIL import Image

st.set_page_config(page_title="Field Processing", page_icon="🌏")

st.write("# Pengolahan Data Survey Lapangan 👨🏽‍💼")

st.sidebar.success("Pilih Detil Parameter.")

st.markdown(
    """
    ##### 1. Informasi lokasi survey terhadap lokasi jaringan seismik eksisting
    ##### 2. Pembuatan Metadata Sensor dan Datalogger (xml file)
    ##### 3. Analisis Power Spectrum Density (PSD) terhadap Noise Model (Peterson Model)
    ##### 4. Analisis HVSR untuk kondisi lokasi survey
    ##### 5. Analisis Velocity Profile (Inversi HVSR)
"""
)

image = Image.open('seismic_vault.png')
st.image(image, caption='Sumber : Site Selection, Preparation and Installation of Seismic Stations \n [Amadej Trnkoczy, Peter Bormann, Winfried Hanka, L. Gary Holcomb and Robert L. Nigbor]')

st.markdown(
    """ 
    ### Link Website 
    - InaTEWS [Indonesia Tsunami Early Warning System](https://inatews.bmkg.go.id/)
    - BMKG [Badan Meteorologi Klimatologi dan Geofisika](https://www.bmkg.go.id/)
    - Webdc BMKG [Access to BMKG Data Archive](https://geof.bmkg.go.id/webdc3/)
"""
)