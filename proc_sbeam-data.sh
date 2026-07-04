#!/bin/sh
# File	: proc_sbeam-data.sh
# By	: MaartenDeBoer.nl, 240801
# Subject	: Script to process SBEAM data for web-page
#(0.2),240802	: Add WWW_UPD
#(0.3),241001	: Upd WWW_DIR, Add FFACE & FSIZE
#(0.4),241101	: Add RCFILE, YR TTL
#(0.5),241101	: Add YR_CNT (disabled) + Some mod's
#(0.6),241230	: Upd's
#
#(0.9),251212
#(0.10),251212	: Renewed with USAGE
#(0.11),260309	: Add CSS for color coding (colors applied by Python post-processor)
PGM=`basename $0|cut -d\. -f1`
VER="0.11"
TMP="/tmp/${PGM}.$$"
CSV="/tmp/${PGM}.csv"
LOG="${HOME}/log/${PGM}.log"
RCFILE="${HOME}/etc/${PGM}.rc"
HOSTNAME=`hostname|cut -d\. -f1`

MONTH_CSV="/tmp/${PGM}_month.csv"
MAILTO="sbeam@agrarix.nl"
MAIL=""

DATA_DIR="/mnt/nas/DATA/SBEAM"
FILTER="2"
PROC_DAYS=""
PROC_MONTHS=""

WWW_UPD=""
WWW_DIR="/mnt/nas/WWW/domains/www.agrarix.net/pages/sbeam"
HTML="${WWW_DIR}/index.html"
FFACE="verdana"
FSIZE=6

USAGE()
{
  echo "Usage: ${PGM} [options]"
  echo "Options            : "
  echo "     -f | --filter : FILTER (${FILTER})"
  echo "     -h            : This help"
  echo "     -d | --days   : Process day file(s)"
  echo "     -p | --proc   : Process month file(s)"
  echo "     -w | --www    : (WW)Web update"
  echo "     -v            : Verbose"
  echo "     -V            : Version"
  echo "     --datadir     : other DATADIR (${DATADIR})"
  echo "     --mailto      : other MAILTO (${MAILTO})"
}
if [ -f ${RCFILE} ]; then
  echo "  RCFILE(${RCFILE}) found. Using it"|tee -a ${LOG}
  . ${RCFILE}
fi  # RCFILE
while [ ${#} -gt 0 ]
do
  case "${1}" in
    '-h')  USAGE; exit 1 ;;
    '-x')  set -x ;;
    '-V')  echo "Version=${VER}" ; exit 1 ;;
    '--datadir')  DATADIR="${2}"; shift  ;;
    '-f'|'--filter') FILTER="${2}"; shift  ;;
    '-d'|'--days') PROC_DAYS=1 ;;
    '-p'|'--proc') PROC_MONTHS=1 ;;
    '--mailto') MAILTO="${2}"; MAIL=1 ; shift  ;;
    '-w'|'--www') WWW_UPD=1 ;;
    *) echo "Option ${1} not found." ; USAGE; exit 1 ;;
  esac
  shift
done


DATI=`date +%Y-%m-%d-%H-%M-%S`
echo "`date` ${PGM} v${VER} started."|tee -a ${LOG}
echo "  CSV=${CSV}|"
echo "  DATA_DIR=${DATA_DIR}|"
echo "  DATI=${DATI}|"
echo "  FILTER=${FILTER}|"
echo "  HOSTNAME=${HOSTNAME}"
echo "  HTML=${HTML}|"
echo "  MAIL=${MAIL}"
echo "  MAILTO=${MAILTO}|"
echo "  MONTH_CSV=${MONTH_CSV}|"
echo "  PROC_DAYS=${PROC_DAYS}"
echo "  PROC_MONTHS=${PROC_MONTHS}"
echo "  RCFILE=${RCFILE}|"
echo "  WWW_DIR=${WWW_DIR}|"
echo "  WWW_UPD=${WWW_UPD}"
sleep 1

if [ ! -d ${DATA_DIR} ]; then
  echo "  NO DATA_DIR (${DATA_DIR}) found. Exiting ..."|tee -a ${LOG}
  exit 4
fi  # <> DATA_DIR
if [ ! -d ${WWW_DIR} ]; then
  echo "  NO WWW_DIR (${WWW_DIR}) found. Exiting ..."|tee -a ${LOG}
  exit 5
fi  # <> DATA_DIR

touch ${TMP}

# ------------------------------------------------------------------
# Proc day files to Months-files
if [ ${PROC_DAYS} ]; then
  echo "  Processing DAY-files in ${DATA_DIR}"|tee -a ${LOG}
  cd ${DATA_DIR}
  ls -1 ??-??-??.CSV|grep "${FILTER}"|while read FNAME
  do
    echo ""
    echo "    ${FNAME}"
    F_YY=`echo ${FNAME}|cut -d\. -f1|cut -d\- -f1`
    F_MM=`echo ${FNAME}|cut -d\. -f1|cut -d\- -f2`
    F_DD=`echo ${FNAME}|cut -d\. -f1|cut -d\- -f3`
    REV_DAY_STR="20${F_YY}-${F_MM}-${F_DD}"
    E_TODAY=`grep "^E-Today kWh;" ${FNAME}|sed 's/
//'|awk -F\; '{print $2}'`
    if [ "${E_TODAY}" = "-,---" ]; then
      E_TODAY=0
    fi
    E_TOTAL=`grep "^E-Total kWh;" ${FNAME}|sed 's/
//'|awk -F\; '{print $2}'`
echo "      E_TODAY=${E_TODAY}| E_TOTAL=${E_TOTAL}|"
#    E_TOTAL=`echo "${E_TOTAL};"|awk -F\; '{print $2}'`
#echo "  E_TOTAL=${E_TOTAL}|"
    OUT_FILE=`echo "E-KWH_20${F_YY}-${F_MM}.CSV"`
#    OUT_FILE=`echo "E-KWH_20${F_YY}.CSV"`
    touch ${OUT_FILE}

    echo "      FNAME=${FNAME} REV_DAY_STR=${REV_DAY_STR} OUT_FILE=${OUT_FILE} E_TODAY=${E_TODAY} E_TOTAL=${E_TOTAL}|"
#    sleep 1

#   If (Jan. / month 01) OUT_FILE is not there, then create with header
    if [ -f ${F_YY}-01.CSV ] && [ ! -f ${OUT_FILE} ]; then
      echo "    Create ${OUT_FILE}"|tee -a ${LOG}
      echo "# DAY ; E_TOTAL ;" > ${OUT_FILE}
    fi  #
    if [ -f ${OUT_FILE} ]; then
      echo "  Writing in ${OUT_FILE}"|tee -a ${LOG}
      echo "${REV_DAY_STR};${E_TOTAL};${E_TODAY};" >> ${OUT_FILE}
    fi  # MND_FILE
  done  # FNAME

fi  # PROC_DAYS

# ----------------------------------------------------------
# Layout
## MONth ; # kWh;
#2025-01;35;
# ...
#2025-12;4;
#2025-gr.ttl;16212;
#2025-Y.ttl;16212;

touch ${TMP}.numbers
if [ ${PROC_MONTHS} ] ; then
  echo "  Processing month-files into MONTH_CSV(${MONTH_CSV}) ..."
  echo "# MONth ; # kWh; " > ${MONTH_CSV}

  PREV_YEAR_NUMBER=0
  LAST_YEAR_NUMBER=0
  YR_CNT=0
  YEAR=2100
  LAST_NUMBER=0

  cd ${DATA_DIR}
  ls -1 E-KWH_20[0-9][0-9]-[01][0-9].CSV|grep "${FILTER}"|while read CSV_FILE
  do
    echo ""
    echo "    CSV_FILE=${CSV_FILE}|"

# Get the last found line of day-01 of this Month file
    FIRST_DAY_LINE=`cat ${CSV_FILE}| grep -v ^#|sort -u|grep -E "^20[0-9][0-9]-[0-9][0-9]-01"|tail -1`
#    echo "    FIRST_DAY_LINE=${FIRST_DAY_LINE}|"

    if [ "${FIRST_DAY_LINE}" != "" ]; then
      FIRST_DATE=`echo ${FIRST_DAY_LINE}|cut -d\; -f1`
      FIRST_NUMBER=`echo ${FIRST_DAY_LINE}|cut -d\; -f2|cut -d\, -f1`
      FIRST_DAY_KWH=`echo ${FIRST_DAY_LINE}|cut -d\; -f3|cut -d\, -f1`
#echo "      FIRST_DATE=${FIRST_DATE}| FIRST_NUMBER=${FIRST_NUMBER}| FIRST_DAY_KWH=${FIRST_DAY_KWH}|"

      if [ "${FIRST_DAY_KWH}" != "" ] && [ "${FIRST_DAY_KWH}" = "-" ]; then
#        FIRST_NUMBER=`cat ${CSV_FILE}|grep -v ^#|grep -v ${SER_NR}|cut -d\; -f2|cut -d\, -f1|grep -v ^\-|grep "^[0-9]"|head -1`
#grep -v ^#|grep -v 2002278782|cut -d\; -f2|cut -d\, -f1|grep -v ^\-|grep "^[0-9]"|head -1
         FIRST_DAY_KWH=0

        echo "    FIRST_DAY_KWH=${FIRST_DAY_KWH}"
      fi

      if [ "${FIRST_NUMBER}" != "" ] && [ "${FIRST_NUMBER}" = "-" ]; then
        FIRST_NUMBER=0
      fi

      LAST_DAY_LINE=`cat ${CSV_FILE}|sort -u| tail -1`
      LAST_DATE=`echo ${LAST_DAY_LINE}|cut -d\; -f1`
      LAST_NUMBER=`echo ${LAST_DAY_LINE}|cut -d\; -f2|cut -d\, -f1`

      echo "      FIRST_DAY_LINE=${FIRST_DAY_LINE}| FIRST_DATE=${FIRST_DATE}| FIRST_NUMBER=${FIRST_NUMBER}| FIRST_DAY_KWH=${FIRST_DAY_KWH}|  "
      echo "      LAST_DAY_LINE=${LAST_DAY_LINE}| LAST_DATE=${LAST_DATE}| LAST_NUMBER=${LAST_NUMBER}"

# Calculate kWh /month
#     The FIRST_NUMBER is kWh at the end of the day. To calculate the stat kWh, you need to substract the day produce from the total dat kWh
      FROM_MON_NUMBER=`expr ${FIRST_NUMBER} - ${FIRST_DAY_KWH}`
      LAST_MON_NUMBER="${LAST_NUMBER}"
      MON_DELTA_NUMBER=`expr ${LAST_MON_NUMBER} - ${FROM_MON_NUMBER}`

      echo "        LAST_MON_NUMBER=${LAST_MON_NUMBER} - FROM_MON_NUMBER=${FROM_MON_NUMBER} := MON_DELTA_NUMBER=${MON_DELTA_NUMBER}"

      YEAR=`echo ${LAST_DATE} |cut -d\- -f1`
      MON=`echo ${LAST_DATE}|cut -d\- -f2`
      echo "${YEAR}-${MON};${MON_DELTA_NUMBER};"|tee -a ${MONTH_CSV}

      echo "YEAR=${YEAR}" > ${TMP}.numbers
      echo "LAST_MON_NUMBER=${LAST_MON_NUMBER}" >> ${TMP}.numbers

      if [ "${MON_DELTA_NUMBER}" != "" ] && [ ${MON_DELTA_NUMBER} -gt 0 ]; then
        YR_CNT=`expr ${YR_CNT} + ${MON_DELTA_NUMBER}`
        echo "        YR_CNT=${YR_CNT} "
      fi  # 
#sleep 1

# Find last total value /year
      if [ "${CSV_FILE}" = "E-KWH_${YEAR}-12.CSV" ]; then
        LAST_YEAR_NUMBER="${LAST_MON_NUMBER}"
        DELTA_YEAR_NUMBER=`expr ${LAST_YEAR_NUMBER} - ${PREV_YEAR_NUMBER}`
#        echo "      ${YEAR}-12 : ${LAST_YEAR_NUMBER} - ${PREV_YEAR_NUMBER} := ${DELTA_YEAR_NUMBER}"

#        echo "${YEAR}-Cnt;${YR_CNT};"|tee -a ${MONTH_CSV}
        echo "${YEAR}-gr.ttl;${LAST_YEAR_NUMBER};"|tee -a ${MONTH_CSV}
        echo "${YEAR}-Y.ttl;${DELTA_YEAR_NUMBER};"|tee -a ${MONTH_CSV}

        PREV_YEAR_NUMBER="${LAST_YEAR_NUMBER}"
        YR_CNT=0
      fi  # CSV_FILE=YEAR}-12.csv

    fi  # ${FIRST_DAY_LINE}" != ""

  done  # CSV_FILE

# Last kWh number
  LAST_MON_NUMBER=`cat ${TMP}.numbers|grep "^LAST_MON_NUMBER"|cut -d\= -f2`
  PREV_YEAR_NUMBER=`cat ${TMP}.numbers|grep "^PREV_YEAR_NUMBER"|cut -d\= -f2`
  YEAR=`cat ${TMP}.numbers|grep "^YEAR"|cut -d\= -f2`
#
#  LAST_GR_TTL_CSV=`grep "*gr.ttl" ${MONTH_CSV}|tail -1`
#  if [ "${LAST_GR_TTL_CSV}" = "" ]; then
#    LAST_GR_TTL_CSV=0
#  fi  # "" 
#  
#  DIFF_YEAR_NUMBER=`expr ${LAST_NUMBER} - ${PREV_YEAR_NUMBER}`
## kWh = gr.ttl (Grant Total)
#echo "LAST_GR_TTL_CSV=${LAST_GR_TTL_CSV}"
#echo "LAST_NUMBER=${LAST_NUMBER}"
#  if [ ${LAST_GR_TTL_CSV} -eq ${LAST_NUMBER} ]; then
## No need for saving. The last 2 CSV-entries are the same.
#    echo "${YEAR}-kWh;${LAST_NUMBER};"|tee -a ${MONTH_CSV}
#    echo "${YEAR}-Ttl;${DIFF_YEAR_NUMBER};"|tee -a ${MONTH_CSV}
#  fi  # LAST .. = LAST
#
  sleep 1

fi  # ! -f ${MONTH_CSV}

# ---------------------------------------------------


## Proc Month_numbers
#echo "# Months =>" > ${TMP} 
#echo -n "   ;" >> ${TMP} 
#
#cat ${MONTH_CSV}|grep -v ^#|cut -d\; -f1|cut -d\- -f2|sort -u|while read MONTH
#do
#  echo -n " ${MONTH} ;"|tee -a ${TMP}
#done  # MONTH
#echo ""|tee -a ${TMP}
#
#cat ${MONTH_CSV}|grep -v ^#|cut -d\; -f1|cut -d\- -f1|sort -u|while read YEAR
#do
#  echo -n "${YEAR};"|tee -a ${TMP}
#  cat ${MONTH_CSV}|grep -v ^#|cut -d\; -f1|cut -d\- -f2|sort -u|while read MONTH
#  do
#    YR_MON_VALUE=`grep "^${YEAR}-${MONTH}" ${MONTH_CSV}|cut -d\; -f2|head -1`
#    echo -n "${YR_MON_VALUE};" |tee -a ${TMP}
#  done  # MONTH
#  echo ""|tee -a ${TMP}
#done  # YEAR
#echo ""|tee -a ${TMP}
#
##cat ${TMP}

# ------------------------------------------------------------------
if [ ${WWW_UPD} ]; then
  echo "  Updating WWW (${HTML})"|tee -a ${LOG}
  echo "<HTML>" > ${HTML}
  echo "  <HEAD>" >> ${HTML}
  echo "  <META NAME=\"generator\" content=\"Agrarix.IT:${PGM} v${VER}\" /> " >> ${HTML}
  echo "  <META NAME=\"up-date\" content=\"${DATI}\" /> " >> ${HTML}
  echo "  </HEAD>" >> ${HTML}
  echo "  <TITLE>SunnyBEAM DATA</TITLE>" >> ${HTML}
  echo "  <LINK REL=\"icon\" HREF=\"Agrarix-Pingu_2017.jpg\" TYPE=\"image/jpg\"> " >> ${HTML}

  echo "  <BODY>" >> ${HTML}

  echo "  <STYLE>" >> ${HTML}
  echo "    body { font-family: verdana; }" >> ${HTML}
  echo "    .kwh-neutral { background-color: #f0f0f0; }" >> ${HTML}
  echo "    .kwh-green { background-color: #90EE90; color: #2d5016; font-weight: bold; }" >> ${HTML}
  echo "    .kwh-orange { background-color: #FFA500; color: #fff; font-weight: bold; }" >> ${HTML}
  echo "    .kwh-equal { background-color: #ADD8E6; color: #003366; font-weight: bold; }" >> ${HTML}
  echo "    table { border-collapse: collapse; margin: 15px 0; }" >> ${HTML}
  echo "    td, th { padding: 8px 12px; border: 1px solid #ddd; }" >> ${HTML}
  echo "    th { background-color: #4CAF50; color: white; }" >> ${HTML}
  echo "  </STYLE>" >> ${HTML}

  echo "    <H1>SunnyBEAM DATA</H1>" >> ${HTML}
  echo "    <H2>Numbers in kWh</H2>" >> ${HTML}
  echo "    <P><FONT SIZE=2><span class=\"kwh-green\">■ Green</span> = higher than last year | <span class=\"kwh-orange\">■ Orange</span> = lower | <span class=\"kwh-equal\">■ Blue</span> = equal</FONT></P>" >> ${HTML}
  echo "    <HR>" >> ${HTML}

  echo "    <TABLE border=1>" >> ${HTML}

  echo "      <TR>" >> ${HTML}
  echo "        <TH><FONT FACE=${FFACE} SIZE=${FSIZE}>YR/mn</FONT></TH>" >> ${HTML}
  cat ${MONTH_CSV}|grep -v ^#|cut -d\; -f1|cut -d\- -f2|sort -u|while read MONTH
  do
    echo "        <TH><FONT FACE=${FFACE} SIZE=${FSIZE}>${MONTH}</FONT></TH>" >> ${HTML}
  done  # MONTH
  echo "      </TR>" >> ${HTML}

  echo "      <TR>" >> ${HTML}

  cat ${MONTH_CSV}|grep -v ^#|cut -d\; -f1|cut -d\- -f1|sort -u|while read YEAR
  do
    echo "${YEAR}"
    echo "        <TD><FONT FACE=${FFACE} SIZE=${FSIZE}>${YEAR}</FONT></TD>"  >> ${HTML}
    cat ${MONTH_CSV}|grep -v ^#|cut -d\; -f1|cut -d\- -f2|sort -u|while read MONTH
    do
      YR_MON_VALUE=`grep "^${YEAR}-${MONTH}" ${MONTH_CSV}|cut -d\; -f2`
      echo "      <TD><FONT FACE=${FFACE} SIZE=${FSIZE}>${YR_MON_VALUE}</FONT></TD>"  >> ${HTML}
    done  # MONTH

    echo "      </TR>"  >> ${HTML}
  done  # YEAR

  echo "    </TABLE>" >> ${HTML}


  echo "<HR>" >> ${HTML}
  echo "  <H6>`date` ${PGM} v${VER} at ${HOSTNAME} </H6>" >> ${HTML}
  echo "  </BODY>" >> ${HTML}
  echo "</HTML>" >> ${HTML}
fi  # WWW_UPD

if [ ${MAIL} ] && [ "${MAILTO}" != "" ]; then
  cp ${TMP} ${CSV}
  date | mailx -s "SunnyBEAM anal [${PGM} v${VER}]" -A ${CSV} "${MAILTO}"
  echo "  Mailed to ${MAILTO}"|tee -a ${LOG}
fi

# ----------------------------------------------------------------------

cat ${TMP}.numbers

rm ${TMP} ${TMP}.numbers
echo "`date` ${PGM} v${VER} finished."|tee -a ${LOG}
exit 0
