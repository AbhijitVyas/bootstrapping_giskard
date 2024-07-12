# FROM intel4coro/base-notebook:20.04-noetic-full-xpra
FROM intel4coro/base-notebook:20.04-noetic

#------------------------------------------rasa38 Conda Env (Python 3.8) for rasa packages------------------------------------------

USER root

RUN conda create -n rasa38 python=3.8 && echo "conda activate rasa38" >> ~/.bashrc

SHELL ["conda", "run", "-n", "rasa38", "/bin/bash", "-c"]

RUN pip install rasa && pip install rasa[spacy] && pip install transformers && pip install nltk

RUN python -m spacy download en_core_web_sm && python -m nltk.downloader punkt && python -m nltk.downloader wordnet

# Initiate RASA workspace 
COPY --chown=${NB_USER}:users binder/rasa.sh /home/${NB_USER}/rasa.sh
RUN chmod +x /home/${NB_USER}/rasa.sh

ENV RASA_WS=/home/${NB_USER}/workspace/rasa
WORKDIR ${RASA_WS}/src
COPY --chown=${NB_USER}:users binder/rasa ${RASA_WS}/src/
RUN chmod -R a+rwx ${PWD}
# SHELL ["conda", "run", "-n", "rasa38", "/bin/bash", "-c"]

#------------------------------------------Switch to base Conda Env (Python 3.10)------------------------------------------

USER root

SHELL ["conda", "run", "-n", "base", "/bin/bash", "-c"]

USER ${NB_USER}

# Initiate ROS workspace 
ENV ROS_WS=/home/${NB_USER}/workspace/ros
WORKDIR ${ROS_WS}/src
# A Workaround for fixing the issue of RvizWeb loading meshes with "file:///" path instead of "package:///".
COPY --chown=${NB_USER}:users binder/me ${ROS_WS}/src/me
COPY --chown=${NB_USER}:users binder/noetic.rosinstall /home/${NB_USER}/noetic.rosinstall
RUN wstool merge /home/${NB_USER}/noetic.rosinstall \
  && wstool update
# Clone repos with ssh url in .gitmodules
RUN git clone https://github.com/maltehue/mujoco_robots.git \
  && cd mujoco_robots \
  && perl -i -p -e 's|git@(.*?):|https://\1/|g' .gitmodules \
  && git submodule sync \
  && git submodule update --init --recursive
RUN git clone https://github.com/HoangGiang93/mujoco_world.git \
  && cd mujoco_world \
  && perl -i -p -e 's|git@(.*?):|https://\1/|g' .gitmodules \
  && git submodule sync \
  && git submodule update --init --recursive

# Install dependencies
WORKDIR  ${ROS_WS}
USER root

RUN rosdep update && apt update && apt dist-upgrade -y \
  && rosdep install -y -r --ignore-src --from-paths . \
  && rosdep fix-permissions \
  && apt install -y ffmpeg libglfw3 libglfw3-dev
USER ${NB_USER}
RUN pip install -r src/giskardpy/requirements.txt

# Install missing python packages (should be included in src/giskardpy/requirements.txt)
RUN pip install termcolor pydot triangle cython~=0.19

# Building Custom bullet3 from source with Python 3.10 (in a clumsy way)
WORKDIR /home/${NB_USER}
RUN git clone https://github.com/pybind/pybind11.git \
  && cd pybind11 \
  && mkdir build \
  && cd build \
  && cmake .. -DCMAKE_BUILD_TYPE=Release -DPYBIND11_PYTHON_VERSION=3 -DPYBIND11_TEST=OFF
USER root
RUN cd pybind11/build && make install
USER ${NB_USER}

RUN git clone https://github.com/SemRoCo/bullet3.git
COPY --chown=${NB_USER}:users binder/build_cmake_pybullet_3.10_double.sh /home/${NB_USER}/bullet3/
USER root
RUN chmod +x /home/${NB_USER}/bullet3/build_cmake_pybullet_3.10_double.sh
RUN cd bullet3 && ./build_cmake_pybullet_3.10_double.sh
USER ${NB_USER}
ENV PYTHONPATH=${PYTHONPATH}:/home/${NB_USER}/bullet3/build_cmake/better_python:/home/${NB_USER}/bullet3/examples/pybullet

# Build ROS workspace
WORKDIR  ${ROS_WS}
# Can not build package iai_pr2_donbot and it is not used
RUN rm -rf src/iai_pr2/iai_pr2_donbot
# Upldate rvizweb
RUN cd src/rvizweb && git pull
RUN catkin build

# Copy the giskard tmp meshes to skip the converting step
COPY --chown=${NB_USER}:users binder/giskard_decomposed_obj ${ROS_WS}/src/giskardpy/tmp
# The giskard standalone does not publish tf messaages by default set it to true for rvizweb
RUN sed -i 's/publish_tf: bool = False/publish_tf: bool = True/g' ${ROS_WS}/src/giskardpy/src/giskardpy/configs/behavior_tree_config.py
# Copy contents of the repo into the image
COPY --chown=${NB_USER}:users . /home/${NB_USER}/bootstrapping_giskard
WORKDIR /home/${NB_USER}/bootstrapping_giskard
RUN git config --global --add safe.directory ${PWD}
# Soft link the ROS workspace directory to the working directory
RUN ln -s ${ROS_WS} ${PWD}/ROS_WS
# jupyterlab interface configuration
COPY --chown=${NB_USER}:users binder/webapps.json ${ROS_WS}/src/rvizweb/webapps/app.json
# COPY --chown=${NB_USER}:users binder/jupyter-settings.json /opt/conda/share/jupyter/lab/settings/overrides.json

# RUN cd ${ROS_WS}/src/rvizweb && git pull

# RUN pip install --upgrade --force-reinstall flask-sqlalchemy sqlalchemy

# RUN cd ${ROS_WS}/src/mujoco_robots && git pull


# -----------------------------------------------------------------------------
# Installing Python dependencies for RASA
RUN pip install spacy && spacy download en_core_web_sm && pip install nltk

RUN python -m nltk.downloader punkt && python -m nltk.downloader wordnet

RUN chmod +x /home/${NB_USER}/bootstrapping_giskard/rasa.sh
RUN wget "https://huggingface.co/google-bert/bert-large-uncased/resolve/main/model.safetensors?download=true" \
  -O ${PWD}/binder/rasa/RASA/models--bert-large-uncased/snapshots/6da4b6a26a1877e173fca3225479512db81a5e5b/model.safetensors

WORKDIR /home/${NB_USER}/bootstrapping_giskard/
RUN ln /home/${NB_USER}/bootstrapping_giskard/binder/rasa/begin_here.ipynb /home/${NB_USER}/bootstrapping_giskard/notebooks/begin.ipynb
# # ------------------------KnowRob Files-------------------------------------------

# # Install SWI Prolog
USER root
RUN apt install -y software-properties-common && \
  apt-add-repository -y ppa:swi-prolog/stable
RUN apt update && \
  apt install -y swi-prolog
ENV SWI_HOME_DIR=/usr/lib/swi-prolog

# # Install MongoDB Community Edition
ARG MONGODEB_VERSION=7.0
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-${MONGODEB_VERSION}.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-${MONGODEB_VERSION}.gpg --dearmor
RUN echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-${MONGODEB_VERSION}.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/${MONGODEB_VERSION} multiverse" | \
    tee /etc/apt/sources.list.d/mongodb-org-${MONGODEB_VERSION}.list
RUN apt update && apt install -y mongodb-org
RUN mkdir -p /data/db && \
    chown -R ${NB_USER}:users /data/db

# # Install Knowrob
USER ${NB_USER}
ENV KNOWROB_WS=${HOME}/workspace/knowrob
RUN mkdir -p ${KNOWROB_WS}/src
WORKDIR ${KNOWROB_WS}/src
RUN wstool init && \
    wstool merge https://raw.github.com/knowrob/knowrob/master/rosinstall/knowrob-base.rosinstall && \
    wstool update

# Switch to root user to install ROS dependencies
USER root
RUN rosdep update && rosdep install -y -r --ignore-src --from-paths . && \
    rosdep fix-permissions

COPY --chown=${NB_USER}:users knowrob_cloud ${KNOWROB_WS}/src/knowrob_cloud
COPY --chown=${NB_USER}:users prolog /prolog

# # Build catkin workspace
USER ${NB_USER}
WORKDIR ${KNOWROB_WS}
RUN source ${ROS_PATH}/setup.bash && catkin_make

# # Source knowrob workspace on a new bash shell
RUN echo "source ${KNOWROB_WS}/devel/setup.bash" >> ${HOME}/.bashrc

# Install jupyter knowrob kernel
USER ${NB_USER}
COPY --chown=${NB_USER}:users . ${HOME}/bootstrapping_giskard
WORKDIR ${HOME}/bootstrapping_giskard
RUN pip install .
COPY --chown=${NB_USER}:users ./kernel.json ${HOME}/.local/share/jupyter/kernels/jknowrob/kernel.json

# Download the example_neem
USER root
RUN mkdir /neem_data && chown ${NB_USER}:users /neem_data
USER ${NB_USER}
RUN cd /neem_data && \
    ln -s /neem_data ${HOME}/bootstrapping_giskard/lectures/data && \
    wget https://nc.uni-bremen.de/index.php/s/Rm4qBTPNDMYXemQ/download -O example_neem.zip && \
    unzip example_neem.zip && \
    mv example_neem/* ./ && \
    rm -r example_neem example_neem.zip

# linraries for querying neem and displaying it
#RUN pip install
#RUN pip install

# libraries for querying the knowledge graph
RUN pip install sos-notebook sos-python sos-papermill sos-r
RUN python -m sos_notebook.install


# jupyterlab interface configuration
COPY --chown=${NB_USER}:users binder/jupyter-settings.json /opt/conda/share/jupyter/lab/settings/overrides.json
# COPY --chown=${NB_USER}:users binder/webapps.json ${ROS_WS}/src/rvizweb/webapps/app.json

# # Entrypoint starting knowrob and mongodb
COPY --chown=${NB_USER}:users binder/entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]

WORKDIR /home/${NB_USER}/bootstrapping_giskard/
# #---------------------------------------------------------------------------------------------------------------------
