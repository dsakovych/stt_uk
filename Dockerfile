FROM ubuntu:18.04

ENV LANG en_US.UTF-8
ENV TZ Etc/UTC
ENV src_path /usr/src
ENV vtt_path $src_path/vtt
ENV KALDI_ROOT $src_path/kaldi

ENV PATH $PATH:$KALDI_ROOT/src/bin:$KALDI_ROOT/tools/openfst/bin:$KALDI_ROOT/src/fstbin/:$KALDI_ROOT/src/gmmbin/
ENV PATH $PATH:$KALDI_ROOT/src/featbin/:$KALDI_ROOT/src/lmbin/:$KALDI_ROOT/src/sgmm2bin/:$KALDI_ROOT/src/fgmmbin/:$KALDI_ROOT/src/latbin/

RUN apt-get update
RUN apt-get install -y python python-pip python-dev
RUN apt-get install -y python3-pip python3-dev python3-virtualenv

RUN apt-get install -y g++ automake autoconf sox libtool subversion gfortran gawk build-essential zlib1g-dev unzip libsox-dev lame flac bc bsdmainutils libicu-dev
RUN apt-get install -y nginx locales supervisor
RUN apt-get install -y iputils-ping wget git nmap

RUN locale-gen en_US.UTF-8
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV cores_for_build 12

###### cloning and building kaldi ######
########################################
RUN mkdir -p $src_path

WORKDIR $src_path
RUN git clone https://github.com/kaldi-asr/kaldi

WORKDIR $KALDI_ROOT/tools
RUN /bin/bash extras/install_openblas.sh
RUN /bin/bash extras/install_mkl.sh
RUN /bin/bash extras/check_dependencies.sh
RUN make -j $cores_for_build
RUN /bin/bash extras/install_irstlm.sh

WORKDIR $KALDI_ROOT/src
RUN ./configure --use-cuda=no --openblas-root=$KALDI_ROOT/tools/OpenBLAS/install
RUN make -j clean depend; make -j 8

WORKDIR $src_path
RUN pip3 install gdown
# download model
RUN gdown https://drive.google.com/uc?id=1Bn4did33DmMk-qmkZxS_3ItqwKv760qL
# download srilm
RUN gdown https://drive.google.com/uc?id=1a9ZEYGdnIpow50_Vid0jG_SbNzFpRN53
RUN cp $src_path/srilm-1.7.2.tar.gz $KALDI_ROOT/tools/srilm.tgz
WORKDIR $KALDI_ROOT/tools/
RUN /bin/bash install_srilm.sh

WORKDIR $src_path
RUN tar -xf kaldi_uk_tri5_ali.tar.xz
RUN mkdir -p $KALDI_ROOT/egs/stt_uk/s5/exp && cp -R exp/. $KALDI_ROOT/egs/stt_uk/s5/exp/.

RUN rm -rf $src_path/data $src_path/exp $src_path/kaldi_uk_tri5_ali.tar.xz $src_path/srilm-1.7.2.tar.gz

COPY kaldi/. $KALDI_ROOT/egs/stt_uk/s5/.

RUN cp -R $KALDI_ROOT/egs/babel/s5d/steps $KALDI_ROOT/egs/stt_uk/s5/steps
RUN cp -R $KALDI_ROOT/egs/babel/s5d/utils $KALDI_ROOT/egs/stt_uk/s5/utils
RUN cp -R $KALDI_ROOT/egs/babel/s5d/local/ $KALDI_ROOT/egs/stt_uk/s5/local/
RUN cp -R $KALDI_ROOT/egs/wsj/s5/local/score.sh $KALDI_ROOT/egs/stt_uk/s5/local/score.sh
########################################
########################################

############## setup nginx ##############
#########################################
RUN rm /etc/nginx/sites-enabled/default
COPY etc/flask.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/flask.conf /etc/nginx/sites-enabled/flask.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
#########################################
#########################################

######### set local conainter tz #########
##########################################
ENV TZ Europe/Kiev
RUN echo $TZ > /etc/timezone && \
apt-get update && apt-get install -y tzdata && \
rm /etc/localtime && \
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
dpkg-reconfigure -f noninteractive tzdata && \
apt-get clean
##########################################
##########################################

####### setup python application #######
########################################
RUN mkdir -p $vtt_path
COPY requirements.txt $vtt_path
RUN pip3 install -r $vtt_path/requirements.txt
COPY . $vtt_path
########################################
########################################

############ setup supervisor ############
##########################################
COPY etc/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN touch /var/run/supervisor.sock
RUN chmod 777 /var/run/supervisor.sock
##########################################
##########################################

EXPOSE 5000

ENTRYPOINT /usr/bin/supervisord -n