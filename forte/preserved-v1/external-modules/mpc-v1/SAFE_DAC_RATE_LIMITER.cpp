/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: SAFE_DAC_RATE_LIMITER
 *** Description: DAC rate limiter with deterministic startup, reset, bounds, and diagnostics
 *** Version:
***     1.0: 2026-07-26/Guilherme -  - 
 *************************************************************************/

#include "SAFE_DAC_RATE_LIMITER.h"
#ifdef FORTE_ENABLE_GENERATED_SOURCE_CPP
#include "SAFE_DAC_RATE_LIMITER_gen.cpp"
#endif


DEFINE_FIRMWARE_FB(FORTE_SAFE_DAC_RATE_LIMITER, g_nStringIdSAFE_DAC_RATE_LIMITER)

const CStringDictionary::TStringId FORTE_SAFE_DAC_RATE_LIMITER::scm_anDataInputNames[] = {g_nStringIdDAC_IN, g_nStringIdMAX_DELTA_DAC, g_nStringIdDAC_MIN, g_nStringIdDAC_MAX, g_nStringIdINITIAL_DAC, g_nStringIdRESET};

const CStringDictionary::TStringId FORTE_SAFE_DAC_RATE_LIMITER::scm_anDataInputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL};

const CStringDictionary::TStringId FORTE_SAFE_DAC_RATE_LIMITER::scm_anDataOutputNames[] = {g_nStringIdDAC_OUT, g_nStringIdLIMITED, g_nStringIdINITIALIZED, g_nStringIdRESET_ACTIVE, g_nStringIdCONFIGURATION_VALID};

const CStringDictionary::TStringId FORTE_SAFE_DAC_RATE_LIMITER::scm_anDataOutputTypeIds[] = {g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdBOOL, g_nStringIdBOOL, g_nStringIdBOOL};

const TDataIOID FORTE_SAFE_DAC_RATE_LIMITER::scm_anEIWith[] = {0, 1, 2, 3, 4, 5, 255};
const TForteInt16 FORTE_SAFE_DAC_RATE_LIMITER::scm_anEIWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_SAFE_DAC_RATE_LIMITER::scm_anEventInputNames[] = {g_nStringIdREQ};

const TDataIOID FORTE_SAFE_DAC_RATE_LIMITER::scm_anEOWith[] = {0, 1, 2, 3, 4, 255};
const TForteInt16 FORTE_SAFE_DAC_RATE_LIMITER::scm_anEOWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_SAFE_DAC_RATE_LIMITER::scm_anEventOutputNames[] = {g_nStringIdCNF};


const SFBInterfaceSpec FORTE_SAFE_DAC_RATE_LIMITER::scm_stFBInterfaceSpec = {
  1, scm_anEventInputNames, scm_anEIWith, scm_anEIWithIndexes,
  1, scm_anEventOutputNames, scm_anEOWith, scm_anEOWithIndexes,
  6, scm_anDataInputNames, scm_anDataInputTypeIds,
  5, scm_anDataOutputNames, scm_anDataOutputTypeIds,
  0, nullptr
};

const CStringDictionary::TStringId FORTE_SAFE_DAC_RATE_LIMITER::scm_anInternalsNames[] = {g_nStringIdprevious_dac, g_nStringIdinitialized_internal, g_nStringIdbounded_input, g_nStringIdbounded_initial, g_nStringIddelta_dac, g_nStringIdlimited_delta};
const CStringDictionary::TStringId FORTE_SAFE_DAC_RATE_LIMITER::scm_anInternalsTypeIds[] = {g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL};
const SInternalVarsInformation FORTE_SAFE_DAC_RATE_LIMITER::scm_stInternalVars = {6, scm_anInternalsNames, scm_anInternalsTypeIds};

void FORTE_SAFE_DAC_RATE_LIMITER::setInitialValues() {
  st_previous_dac() = 0.0;
  st_initialized_internal() = false;
  st_bounded_input() = 0.0;
  st_bounded_initial() = 0.0;
  st_delta_dac() = 0.0;
  st_limited_delta() = 0.0;
}

void FORTE_SAFE_DAC_RATE_LIMITER::alg_SAFE_DAC_RATE_LIMITER_ALGORITHM(void) {
  st_CONFIGURATION_VALID() = ((st_MAX_DELTA_DAC() > 0.0) && (st_DAC_MIN() < st_DAC_MAX()));
  if((! st_CONFIGURATION_VALID())) {
  	st_previous_dac() = 0.0;
  	st_initialized_internal() = false;
  	st_DAC_OUT() = 0.0;
  	st_LIMITED() = true;
  	st_INITIALIZED() = false;
  	st_RESET_ACTIVE() = false;
  }
  else {
  	st_bounded_initial() = st_INITIAL_DAC();
  	if((st_bounded_initial() > st_DAC_MAX())) {
  		st_bounded_initial() = st_DAC_MAX();
  	}
  	else if((st_bounded_initial() < st_DAC_MIN())) {
  		st_bounded_initial() = st_DAC_MIN();
  	}
  	if((st_RESET() || (! st_initialized_internal()))) {
  		st_previous_dac() = st_bounded_initial();
  		st_DAC_OUT() = st_previous_dac();
  		st_initialized_internal() = true;
  		st_LIMITED() = (st_DAC_OUT() != st_DAC_IN());
  		st_INITIALIZED() = true;
  		st_RESET_ACTIVE() = st_RESET();
  	}
  	else {
  		st_bounded_input() = st_DAC_IN();
  		if((st_bounded_input() > st_DAC_MAX())) {
  			st_bounded_input() = st_DAC_MAX();
  		}
  		else if((st_bounded_input() < st_DAC_MIN())) {
  			st_bounded_input() = st_DAC_MIN();
  		}
  		st_delta_dac() = SUB(st_bounded_input(), st_previous_dac());
  		if((st_delta_dac() > st_MAX_DELTA_DAC())) {
  			st_limited_delta() = st_MAX_DELTA_DAC();
  		}
  		else if((st_delta_dac() < (- st_MAX_DELTA_DAC()))) {
  			st_limited_delta() = (- st_MAX_DELTA_DAC());
  		}
  		else {
  			st_limited_delta() = st_delta_dac();
  		}
  		st_DAC_OUT() = ADD(st_previous_dac(), st_limited_delta());
  		if((st_DAC_OUT() > st_DAC_MAX())) {
  			st_DAC_OUT() = st_DAC_MAX();
  		}
  		else if((st_DAC_OUT() < st_DAC_MIN())) {
  			st_DAC_OUT() = st_DAC_MIN();
  		}
  		st_previous_dac() = st_DAC_OUT();
  		st_LIMITED() = (st_DAC_OUT() != st_DAC_IN());
  		st_INITIALIZED() = true;
  		st_RESET_ACTIVE() = false;
  	}
  }
}


void FORTE_SAFE_DAC_RATE_LIMITER::enterStateSTART(void) {
  m_nECCState = scm_nStateSTART;
}

void FORTE_SAFE_DAC_RATE_LIMITER::enterStateCALCULATE(void) {
  m_nECCState = scm_nStateCALCULATE;
  alg_SAFE_DAC_RATE_LIMITER_ALGORITHM();
}

void FORTE_SAFE_DAC_RATE_LIMITER::enterStateCONFIRM(void) {
  m_nECCState = scm_nStateCONFIRM;
  sendOutputEvent(scm_nEventCNFID);
}


void FORTE_SAFE_DAC_RATE_LIMITER::executeEvent(int pa_nEIID){
  bool bTransitionCleared;
  do {
    bTransitionCleared = true;
    switch(m_nECCState) {
      case scm_nStateSTART:
        if(scm_nEventREQID == pa_nEIID)
          enterStateCALCULATE();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      case scm_nStateCALCULATE:
        if(1)
          enterStateCONFIRM();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      case scm_nStateCONFIRM:
        if(1)
          enterStateSTART();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      default:
        DEVLOG_ERROR("The state is not in the valid range! The state value is: %d. The max value can be: 3.", m_nECCState.operator TForteUInt16 ());
        m_nECCState = 0; // 0 is always the initial state
        break;
    }
    pa_nEIID = cg_nInvalidEventID; // we have to clear the event after the first check in order to ensure correct behavior
  } while(bTransitionCleared);
}


