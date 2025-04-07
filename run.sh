#!/bin/bash

docker run -d -p 8501:8501 --restart=always -e ENABLE_ACCESS_LOG=Y -v /data/streamlit-play/log:/log --name streamlit_play streamlit-play
