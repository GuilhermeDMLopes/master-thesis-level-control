/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: MPC_MEDIAN_FILTER_9
 *** Description: Deterministic 9-sample rolling median for the raw-count MPC model coordinate
 *** Version:
***     1.0: 2026-08-10/Guilherme -  - 
 *************************************************************************/

#include "MPC_MEDIAN_FILTER_9.h"
#ifdef FORTE_ENABLE_GENERATED_SOURCE_CPP
#include "MPC_MEDIAN_FILTER_9_gen.cpp"
#endif


DEFINE_FIRMWARE_FB(FORTE_MPC_MEDIAN_FILTER_9, g_nStringIdMPC_MEDIAN_FILTER_9)

const CStringDictionary::TStringId FORTE_MPC_MEDIAN_FILTER_9::scm_anDataInputNames[] = {g_nStringIdPV_RAW, g_nStringIdRESET};

const CStringDictionary::TStringId FORTE_MPC_MEDIAN_FILTER_9::scm_anDataInputTypeIds[] = {g_nStringIdLREAL, g_nStringIdBOOL};

const CStringDictionary::TStringId FORTE_MPC_MEDIAN_FILTER_9::scm_anDataOutputNames[] = {g_nStringIdPV_MEDIAN, g_nStringIdINITIALIZED};

const CStringDictionary::TStringId FORTE_MPC_MEDIAN_FILTER_9::scm_anDataOutputTypeIds[] = {g_nStringIdLREAL, g_nStringIdBOOL};

const TDataIOID FORTE_MPC_MEDIAN_FILTER_9::scm_anEIWith[] = {0, 1, 255};
const TForteInt16 FORTE_MPC_MEDIAN_FILTER_9::scm_anEIWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_MPC_MEDIAN_FILTER_9::scm_anEventInputNames[] = {g_nStringIdREQ};

const TDataIOID FORTE_MPC_MEDIAN_FILTER_9::scm_anEOWith[] = {0, 1, 255};
const TForteInt16 FORTE_MPC_MEDIAN_FILTER_9::scm_anEOWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_MPC_MEDIAN_FILTER_9::scm_anEventOutputNames[] = {g_nStringIdCNF};


const SFBInterfaceSpec FORTE_MPC_MEDIAN_FILTER_9::scm_stFBInterfaceSpec = {
  1, scm_anEventInputNames, scm_anEIWith, scm_anEIWithIndexes,
  1, scm_anEventOutputNames, scm_anEOWith, scm_anEOWithIndexes,
  2, scm_anDataInputNames, scm_anDataInputTypeIds,
  2, scm_anDataOutputNames, scm_anDataOutputTypeIds,
  0, nullptr
};

const CStringDictionary::TStringId FORTE_MPC_MEDIAN_FILTER_9::scm_anInternalsNames[] = {g_nStringIdinitialized_internal, g_nStringIdv0, g_nStringIdv1, g_nStringIdv2, g_nStringIdv3, g_nStringIdv4, g_nStringIdv5, g_nStringIdv6, g_nStringIdv7, g_nStringIdv8, g_nStringIds0, g_nStringIds1, g_nStringIds2, g_nStringIds3, g_nStringIds4, g_nStringIds5, g_nStringIds6, g_nStringIds7, g_nStringIds8, g_nStringIdswap_value};
const CStringDictionary::TStringId FORTE_MPC_MEDIAN_FILTER_9::scm_anInternalsTypeIds[] = {g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL};
const SInternalVarsInformation FORTE_MPC_MEDIAN_FILTER_9::scm_stInternalVars = {20, scm_anInternalsNames, scm_anInternalsTypeIds};

void FORTE_MPC_MEDIAN_FILTER_9::setInitialValues() {
  st_initialized_internal() = false;
  st_v0() = 0.0;
  st_v1() = 0.0;
  st_v2() = 0.0;
  st_v3() = 0.0;
  st_v4() = 0.0;
  st_v5() = 0.0;
  st_v6() = 0.0;
  st_v7() = 0.0;
  st_v8() = 0.0;
  st_s0() = 0.0;
  st_s1() = 0.0;
  st_s2() = 0.0;
  st_s3() = 0.0;
  st_s4() = 0.0;
  st_s5() = 0.0;
  st_s6() = 0.0;
  st_s7() = 0.0;
  st_s8() = 0.0;
  st_swap_value() = 0.0;
}

void FORTE_MPC_MEDIAN_FILTER_9::alg_ALG_MEDIAN(void) {
  if((st_RESET() || (! st_initialized_internal()))) {
  	st_v0() = st_PV_RAW();
  	st_v1() = st_PV_RAW();
  	st_v2() = st_PV_RAW();
  	st_v3() = st_PV_RAW();
  	st_v4() = st_PV_RAW();
  	st_v5() = st_PV_RAW();
  	st_v6() = st_PV_RAW();
  	st_v7() = st_PV_RAW();
  	st_v8() = st_PV_RAW();
  	st_initialized_internal() = true;
  }
  else {
  	st_v0() = st_v1();
  	st_v1() = st_v2();
  	st_v2() = st_v3();
  	st_v3() = st_v4();
  	st_v4() = st_v5();
  	st_v5() = st_v6();
  	st_v6() = st_v7();
  	st_v7() = st_v8();
  	st_v8() = st_PV_RAW();
  }
  st_s0() = st_v0();
  st_s1() = st_v1();
  st_s2() = st_v2();
  st_s3() = st_v3();
  st_s4() = st_v4();
  st_s5() = st_v5();
  st_s6() = st_v6();
  st_s7() = st_v7();
  st_s8() = st_v8();
  if((st_s0() > st_s1())) {
  	st_swap_value() = st_s0();
  	st_s0() = st_s1();
  	st_s1() = st_swap_value();
  }
  if((st_s2() > st_s3())) {
  	st_swap_value() = st_s2();
  	st_s2() = st_s3();
  	st_s3() = st_swap_value();
  }
  if((st_s4() > st_s5())) {
  	st_swap_value() = st_s4();
  	st_s4() = st_s5();
  	st_s5() = st_swap_value();
  }
  if((st_s6() > st_s7())) {
  	st_swap_value() = st_s6();
  	st_s6() = st_s7();
  	st_s7() = st_swap_value();
  }
  if((st_s1() > st_s2())) {
  	st_swap_value() = st_s1();
  	st_s1() = st_s2();
  	st_s2() = st_swap_value();
  }
  if((st_s3() > st_s4())) {
  	st_swap_value() = st_s3();
  	st_s3() = st_s4();
  	st_s4() = st_swap_value();
  }
  if((st_s5() > st_s6())) {
  	st_swap_value() = st_s5();
  	st_s5() = st_s6();
  	st_s6() = st_swap_value();
  }
  if((st_s7() > st_s8())) {
  	st_swap_value() = st_s7();
  	st_s7() = st_s8();
  	st_s8() = st_swap_value();
  }
  if((st_s0() > st_s1())) {
  	st_swap_value() = st_s0();
  	st_s0() = st_s1();
  	st_s1() = st_swap_value();
  }
  if((st_s2() > st_s3())) {
  	st_swap_value() = st_s2();
  	st_s2() = st_s3();
  	st_s3() = st_swap_value();
  }
  if((st_s4() > st_s5())) {
  	st_swap_value() = st_s4();
  	st_s4() = st_s5();
  	st_s5() = st_swap_value();
  }
  if((st_s6() > st_s7())) {
  	st_swap_value() = st_s6();
  	st_s6() = st_s7();
  	st_s7() = st_swap_value();
  }
  if((st_s1() > st_s2())) {
  	st_swap_value() = st_s1();
  	st_s1() = st_s2();
  	st_s2() = st_swap_value();
  }
  if((st_s3() > st_s4())) {
  	st_swap_value() = st_s3();
  	st_s3() = st_s4();
  	st_s4() = st_swap_value();
  }
  if((st_s5() > st_s6())) {
  	st_swap_value() = st_s5();
  	st_s5() = st_s6();
  	st_s6() = st_swap_value();
  }
  if((st_s7() > st_s8())) {
  	st_swap_value() = st_s7();
  	st_s7() = st_s8();
  	st_s8() = st_swap_value();
  }
  if((st_s0() > st_s1())) {
  	st_swap_value() = st_s0();
  	st_s0() = st_s1();
  	st_s1() = st_swap_value();
  }
  if((st_s2() > st_s3())) {
  	st_swap_value() = st_s2();
  	st_s2() = st_s3();
  	st_s3() = st_swap_value();
  }
  if((st_s4() > st_s5())) {
  	st_swap_value() = st_s4();
  	st_s4() = st_s5();
  	st_s5() = st_swap_value();
  }
  if((st_s6() > st_s7())) {
  	st_swap_value() = st_s6();
  	st_s6() = st_s7();
  	st_s7() = st_swap_value();
  }
  if((st_s1() > st_s2())) {
  	st_swap_value() = st_s1();
  	st_s1() = st_s2();
  	st_s2() = st_swap_value();
  }
  if((st_s3() > st_s4())) {
  	st_swap_value() = st_s3();
  	st_s3() = st_s4();
  	st_s4() = st_swap_value();
  }
  if((st_s5() > st_s6())) {
  	st_swap_value() = st_s5();
  	st_s5() = st_s6();
  	st_s6() = st_swap_value();
  }
  if((st_s7() > st_s8())) {
  	st_swap_value() = st_s7();
  	st_s7() = st_s8();
  	st_s8() = st_swap_value();
  }
  if((st_s0() > st_s1())) {
  	st_swap_value() = st_s0();
  	st_s0() = st_s1();
  	st_s1() = st_swap_value();
  }
  if((st_s2() > st_s3())) {
  	st_swap_value() = st_s2();
  	st_s2() = st_s3();
  	st_s3() = st_swap_value();
  }
  if((st_s4() > st_s5())) {
  	st_swap_value() = st_s4();
  	st_s4() = st_s5();
  	st_s5() = st_swap_value();
  }
  if((st_s6() > st_s7())) {
  	st_swap_value() = st_s6();
  	st_s6() = st_s7();
  	st_s7() = st_swap_value();
  }
  if((st_s1() > st_s2())) {
  	st_swap_value() = st_s1();
  	st_s1() = st_s2();
  	st_s2() = st_swap_value();
  }
  if((st_s3() > st_s4())) {
  	st_swap_value() = st_s3();
  	st_s3() = st_s4();
  	st_s4() = st_swap_value();
  }
  if((st_s5() > st_s6())) {
  	st_swap_value() = st_s5();
  	st_s5() = st_s6();
  	st_s6() = st_swap_value();
  }
  if((st_s7() > st_s8())) {
  	st_swap_value() = st_s7();
  	st_s7() = st_s8();
  	st_s8() = st_swap_value();
  }
  if((st_s0() > st_s1())) {
  	st_swap_value() = st_s0();
  	st_s0() = st_s1();
  	st_s1() = st_swap_value();
  }
  if((st_s2() > st_s3())) {
  	st_swap_value() = st_s2();
  	st_s2() = st_s3();
  	st_s3() = st_swap_value();
  }
  if((st_s4() > st_s5())) {
  	st_swap_value() = st_s4();
  	st_s4() = st_s5();
  	st_s5() = st_swap_value();
  }
  if((st_s6() > st_s7())) {
  	st_swap_value() = st_s6();
  	st_s6() = st_s7();
  	st_s7() = st_swap_value();
  }
  st_PV_MEDIAN() = st_s4();
  st_INITIALIZED() = st_initialized_internal();
}


void FORTE_MPC_MEDIAN_FILTER_9::enterStateSTART(void) {
  m_nECCState = scm_nStateSTART;
}

void FORTE_MPC_MEDIAN_FILTER_9::enterStateEXEC(void) {
  m_nECCState = scm_nStateEXEC;
  alg_ALG_MEDIAN();
  sendOutputEvent(scm_nEventCNFID);
}


void FORTE_MPC_MEDIAN_FILTER_9::executeEvent(int pa_nEIID){
  bool bTransitionCleared;
  do {
    bTransitionCleared = true;
    switch(m_nECCState) {
      case scm_nStateSTART:
        if(scm_nEventREQID == pa_nEIID)
          enterStateEXEC();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      case scm_nStateEXEC:
        if(1)
          enterStateSTART();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      default:
        DEVLOG_ERROR("The state is not in the valid range! The state value is: %d. The max value can be: 2.", m_nECCState.operator TForteUInt16 ());
        m_nECCState = 0; // 0 is always the initial state
        break;
    }
    pa_nEIID = cg_nInvalidEventID; // we have to clear the event after the first check in order to ensure correct behavior
  } while(bTransitionCleared);
}


