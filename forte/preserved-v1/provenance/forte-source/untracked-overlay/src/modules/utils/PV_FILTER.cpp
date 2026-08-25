/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: PV_FILTER
 *** Description: Basic FB with empty ECC
 *** Version:
***     1.0: 2026-04-29/guilh -  - 
 *************************************************************************/

#include "PV_FILTER.h"
#ifdef FORTE_ENABLE_GENERATED_SOURCE_CPP
#include "PV_FILTER_gen.cpp"
#endif


DEFINE_FIRMWARE_FB(FORTE_PV_FILTER, g_nStringIdPV_FILTER)

const CStringDictionary::TStringId FORTE_PV_FILTER::scm_anDataInputNames[] = {g_nStringIdPV_IN, g_nStringIdALPHA, g_nStringIdRESET};

const CStringDictionary::TStringId FORTE_PV_FILTER::scm_anDataInputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL};

const CStringDictionary::TStringId FORTE_PV_FILTER::scm_anDataOutputNames[] = {g_nStringIdPV_OUT};

const CStringDictionary::TStringId FORTE_PV_FILTER::scm_anDataOutputTypeIds[] = {g_nStringIdLREAL};

const TDataIOID FORTE_PV_FILTER::scm_anEIWith[] = {0, 1, 2, 255};
const TForteInt16 FORTE_PV_FILTER::scm_anEIWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_PV_FILTER::scm_anEventInputNames[] = {g_nStringIdREQ};

const TDataIOID FORTE_PV_FILTER::scm_anEOWith[] = {0, 255};
const TForteInt16 FORTE_PV_FILTER::scm_anEOWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_PV_FILTER::scm_anEventOutputNames[] = {g_nStringIdCNF};


const SFBInterfaceSpec FORTE_PV_FILTER::scm_stFBInterfaceSpec = {
  1, scm_anEventInputNames, scm_anEIWith, scm_anEIWithIndexes,
  1, scm_anEventOutputNames, scm_anEOWith, scm_anEOWithIndexes,
  3, scm_anDataInputNames, scm_anDataInputTypeIds,
  1, scm_anDataOutputNames, scm_anDataOutputTypeIds,
  0, nullptr
};

const CStringDictionary::TStringId FORTE_PV_FILTER::scm_anInternalsNames[] = {g_nStringIdinitialized, g_nStringIdalpha_limited};
const CStringDictionary::TStringId FORTE_PV_FILTER::scm_anInternalsTypeIds[] = {g_nStringIdBOOL, g_nStringIdLREAL};
const SInternalVarsInformation FORTE_PV_FILTER::scm_stInternalVars = {2, scm_anInternalsNames, scm_anInternalsTypeIds};

void FORTE_PV_FILTER::setInitialValues() {
}

void FORTE_PV_FILTER::alg_ALG_FILTER(void) {
  if(st_RESET()) {
  	st_PV_OUT() = st_PV_IN();
  	st_initialized() = true;
  }
  else {
  	if((! st_initialized())) {
  		st_PV_OUT() = st_PV_IN();
  		st_initialized() = true;
  	}
  	else {
  		st_alpha_limited() = st_ALPHA();
  		if((st_alpha_limited() < 0.0)) {
  			st_alpha_limited() = 0.0;
  		}
  		else if((st_alpha_limited() > 1.0)) {
  			st_alpha_limited() = 1.0;
  		}
  		st_PV_OUT() = ADD(MUL(st_alpha_limited(), st_PV_OUT()), MUL(SUB(1.0, st_alpha_limited()), st_PV_IN()));
  	}
  }
}


void FORTE_PV_FILTER::enterStateSTART(void) {
  m_nECCState = scm_nStateSTART;
}

void FORTE_PV_FILTER::enterStateFILTER(void) {
  m_nECCState = scm_nStateFILTER;
  alg_ALG_FILTER();
}

void FORTE_PV_FILTER::enterStateDONE(void) {
  m_nECCState = scm_nStateDONE;
  sendOutputEvent(scm_nEventCNFID);
}


void FORTE_PV_FILTER::executeEvent(int pa_nEIID){
  bool bTransitionCleared;
  do {
    bTransitionCleared = true;
    switch(m_nECCState) {
      case scm_nStateSTART:
        if(scm_nEventREQID == pa_nEIID)
          enterStateFILTER();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      case scm_nStateFILTER:
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


