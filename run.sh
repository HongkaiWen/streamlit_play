#!/bin/bash

docker run -d -p 8501:8501 --restart=always --name streamlit_play streamlit-play
