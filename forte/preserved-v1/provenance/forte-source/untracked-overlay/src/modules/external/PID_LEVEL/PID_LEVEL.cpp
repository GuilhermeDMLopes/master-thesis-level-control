/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: PID_LEVEL
 *** Description: Basic FB with empty ECC
 *** Version:
***     1.0: 2026-03-26/guilh -  - 
 *************************************************************************/

#include "PID_LEVEL.h"
#ifdef FORTE_ENABLE_GENERATED_SOURCE_CPP
#include "PID_LEVEL_gen.cpp"
#endif


DEFINE_FIRMWARE_FB(FORTE_PID_LEVEL, g_nStringIdPID_LEVEL)

const CStringDictionary::TStringId FORTE_PID_LEVEL::scm_anDataInputNames[] = {g_nStringIdPV, g_nStringIdSP, g_nStringIdKP, g_nStringIdKI, g_nStringIdKD, g_nStringIdTS, g_nStringIdMANUAL, g_nStringIdMAN_OUT, g_nStringIdRESET};

const CStringDictionary::TStringId FORTE_PID_LEVEL::scm_anDataInputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdBOOL};

const CStringDictionary::TStringId FORTE_PID_LEVEL::scm_anDataOutputNames[] = {g_nStringIdMV, g_nStringIdERR, g_nStringIdP_TERM, g_nStringIdI_TERM, g_nStringIdD_TERM};

const CStringDictionary::TStringId FORTE_PID_LEVEL::scm_anDataOutputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL};

const TDataIOID FORTE_PID_LEVEL::scm_anEIWith[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 255};
const TForteInt16 FORTE_PID_LEVEL::scm_anEIWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_PID_LEVEL::scm_anEventInputNames[] = {g_nStringIdREQ};

const TDataIOID FORTE_PID_LEVEL::scm_anEOWith[] = {0, 1, 2, 3, 4, 255};
const TForteInt16 FORTE_PID_LEVEL::scm_anEOWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_PID_LEVEL::scm_anEventOutputNames[] = {g_nStringIdCNF};


const SFBInterfaceSpec FORTE_PID_LEVEL::scm_stFBInterfaceSpec = {
  1, scm_anEventInputNames, scm_anEIWith, scm_anEIWithIndexes,
  1, scm_anEventOutputNames, scm_anEOWith, scm_anEOWithIndexes,
  9, scm_anDataInputNames, scm_anDataInputTypeIds,
  5, scm_anDataOutputNames, scm_anDataOutputTypeIds,
  0, nullptr
};

const CStringDictionary::TStringId FORTE_PID_LEVEL::scm_anInternalsNames[] = {g_nStringIde_prev, g_nStringIdi_acc, g_nStringIdu_raw};
const CStringDictionary::TStringId FORTE_PID_LEVEL::scm_anInternalsTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL};
const SInternalVarsInformation FORTE_PID_LEVEL::scm_stInternalVars = {3, scm_anInternalsNames, scm_anInternalsTypeIds};

void FORTE_PID_LEVEL::setInitialValues() {
  st_e_prev() = 0.0;
  st_i_acc() = 0.0;
  st_u_raw() = 0.0;
}

void FORTE_PID_LEVEL::alg_ALG_PID(void) {
  if(st_RESET()) {
  	st_i_acc() = 0.0;
  	st_e_prev() = 0.0;
  }
  if(st_MANUAL()) {
  	st_MV() = st_MAN_OUT();
  	if((st_MV() > 100.0)) {
  		st_MV() = 100.0;
  	}
  	else if((st_MV() < 0.0)) {
  		st_MV() = 0.0;
  	}
  	st_ERR() = SUB(st_SP(), st_PV());
  	st_P_TERM() = 0.0;
  	st_I_TERM() = 0.0;
  	st_D_TERM() = 0.0;
  }
  else {
  	st_ERR() = SUB(st_SP(), st_PV());
  	st_P_TERM() = MUL(st_KP(), st_ERR());
  	st_i_acc() = ADD(st_i_acc(), MUL(st_ERR(), st_TS()));
  	st_I_TERM() = MUL(st_KI(), st_i_acc());
  	st_D_TERM() = MUL(st_KD(), DIV(SUB(st_ERR(), st_e_prev()), st_TS()));
  	st_u_raw() = ADD(ADD(st_P_TERM(), st_I_TERM()), st_D_TERM());
  	if((st_u_raw() > 100.0)) {
  		st_MV() = 100.0;
  	}
  	else if((st_u_raw() < 0.0)) {
  		st_MV() = 0.0;
  	}
  	else {
  		st_MV() = st_u_raw();
  	}
  	st_e_prev() = st_ERR();
  }
}


void FORTE_PID_LEVEL::enterStateSTART(void) {
  m_nECCState = scm_nStateSTART;
}

void FORTE_PID_LEVEL::enterStateCALC(void) {
  m_nECCState = scm_nStateCALC;
  alg_ALG_PID();
}

void FORTE_PID_LEVEL::enterStateDONE(void) {
  m_nECCState = scm_nStateDONE;
  sendOutputEvent(scm_nEventCNFID);
}


void FORTE_PID_LEVEL::executeEvent(int pa_nEIID){
  bool bTransitionCleared;
  do {
    bTransitionCleared = true;
    switch(m_nECCState) {
      case scm_nStateSTART:
        if(scm_nEventREQID == pa_nEIID)
          enterStateCALC();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      case scm_nStateCALC:
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


