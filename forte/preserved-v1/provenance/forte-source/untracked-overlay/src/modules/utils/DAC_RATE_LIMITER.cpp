/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: DAC_RATE_LIMITER
 *** Description: Basic FB with empty ECC
 *** Version:
***     1.0: 2026-04-29/guilh -  - 
 *************************************************************************/

#include "DAC_RATE_LIMITER.h"
#ifdef FORTE_ENABLE_GENERATED_SOURCE_CPP
#include "DAC_RATE_LIMITER_gen.cpp"
#endif


DEFINE_FIRMWARE_FB(FORTE_DAC_RATE_LIMITER, g_nStringIdDAC_RATE_LIMITER)

const CStringDictionary::TStringId FORTE_DAC_RATE_LIMITER::scm_anDataInputNames[] = {g_nStringIdDAC_IN, g_nStringIdMAX_DELTA_DAC, g_nStringIdDAC_MIN, g_nStringIdDAC_MAX, g_nStringIdRESET};

const CStringDictionary::TStringId FORTE_DAC_RATE_LIMITER::scm_anDataInputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL};

const CStringDictionary::TStringId FORTE_DAC_RATE_LIMITER::scm_anDataOutputNames[] = {g_nStringIdDAC_OUT};

const CStringDictionary::TStringId FORTE_DAC_RATE_LIMITER::scm_anDataOutputTypeIds[] = {g_nStringIdLREAL};

const TDataIOID FORTE_DAC_RATE_LIMITER::scm_anEIWith[] = {0, 1, 2, 3, 4, 255};
const TForteInt16 FORTE_DAC_RATE_LIMITER::scm_anEIWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_DAC_RATE_LIMITER::scm_anEventInputNames[] = {g_nStringIdREQ};

const TDataIOID FORTE_DAC_RATE_LIMITER::scm_anEOWith[] = {0, 255};
const TForteInt16 FORTE_DAC_RATE_LIMITER::scm_anEOWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_DAC_RATE_LIMITER::scm_anEventOutputNames[] = {g_nStringIdCNF};


const SFBInterfaceSpec FORTE_DAC_RATE_LIMITER::scm_stFBInterfaceSpec = {
  1, scm_anEventInputNames, scm_anEIWith, scm_anEIWithIndexes,
  1, scm_anEventOutputNames, scm_anEOWith, scm_anEOWithIndexes,
  5, scm_anDataInputNames, scm_anDataInputTypeIds,
  1, scm_anDataOutputNames, scm_anDataOutputTypeIds,
  0, nullptr
};

const CStringDictionary::TStringId FORTE_DAC_RATE_LIMITER::scm_anInternalsNames[] = {g_nStringIdlast_dac, g_nStringIddelta, g_nStringIdinitialized};
const CStringDictionary::TStringId FORTE_DAC_RATE_LIMITER::scm_anInternalsTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL};
const SInternalVarsInformation FORTE_DAC_RATE_LIMITER::scm_stInternalVars = {3, scm_anInternalsNames, scm_anInternalsTypeIds};

void FORTE_DAC_RATE_LIMITER::setInitialValues() {
}

void FORTE_DAC_RATE_LIMITER::alg_ALG_LIMIT(void) {
  if(st_RESET()) {
  	st_last_dac() = st_DAC_IN();
  	st_DAC_OUT() = st_DAC_IN();
  	st_initialized() = true;
  }
  else {
  	if((! st_initialized())) {
  		st_last_dac() = st_DAC_IN();
  		st_DAC_OUT() = st_DAC_IN();
  		st_initialized() = true;
  	}
  	else {
  		st_delta() = SUB(st_DAC_IN(), st_last_dac());
  		if((st_delta() > st_MAX_DELTA_DAC())) {
  			st_DAC_OUT() = ADD(st_last_dac(), st_MAX_DELTA_DAC());
  		}
  		else if((st_delta() < (- st_MAX_DELTA_DAC()))) {
  			st_DAC_OUT() = SUB(st_last_dac(), st_MAX_DELTA_DAC());
  		}
  		else {
  			st_DAC_OUT() = st_DAC_IN();
  		}
  		if((st_DAC_OUT() > st_DAC_MAX())) {
  			st_DAC_OUT() = st_DAC_MAX();
  		}
  		else if((st_DAC_OUT() < st_DAC_MIN())) {
  			st_DAC_OUT() = st_DAC_MIN();
  		}
  		st_last_dac() = st_DAC_OUT();
  	}
  }
}


void FORTE_DAC_RATE_LIMITER::enterStateSTART(void) {
  m_nECCState = scm_nStateSTART;
}

void FORTE_DAC_RATE_LIMITER::enterStateLIMIT(void) {
  m_nECCState = scm_nStateLIMIT;
  alg_ALG_LIMIT();
}

void FORTE_DAC_RATE_LIMITER::enterStateDONE(void) {
  m_nECCState = scm_nStateDONE;
  sendOutputEvent(scm_nEventCNFID);
}


void FORTE_DAC_RATE_LIMITER::executeEvent(int pa_nEIID){
  bool bTransitionCleared;
  do {
    bTransitionCleared = true;
    switch(m_nECCState) {
      case scm_nStateSTART:
        if(scm_nEventREQID == pa_nEIID)
          enterStateLIMIT();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      case scm_nStateLIMIT:
        if(1)
          enterStateDONE();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      case scm_nStateDONE:
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


