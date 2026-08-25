/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: MPC_LEVEL
 *** Description: Basic FB with empty ECC
 *** Version:
***     1.0: 2026-04-25/guilh -  - 
 *************************************************************************/

#include "MPC_LEVEL.h"
#ifdef FORTE_ENABLE_GENERATED_SOURCE_CPP
#include "MPC_LEVEL_gen.cpp"
#endif


DEFINE_FIRMWARE_FB(FORTE_MPC_LEVEL, g_nStringIdMPC_LEVEL)

const CStringDictionary::TStringId FORTE_MPC_LEVEL::scm_anDataInputNames[] = {g_nStringIdPV, g_nStringIdSP, g_nStringIdA, g_nStringIdB, g_nStringIdC, g_nStringIdHORIZON, g_nStringIdDAC_MIN, g_nStringIdDAC_MAX, g_nStringIdDAC_STEP, g_nStringIdLAMBDA_DU, g_nStringIdENABLE, g_nStringIdRESET};

const CStringDictionary::TStringId FORTE_MPC_LEVEL::scm_anDataInputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdUINT, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdBOOL};

const CStringDictionary::TStringId FORTE_MPC_LEVEL::scm_anDataOutputNames[] = {g_nStringIdDAC_OUT, g_nStringIdMV_PERCENT, g_nStringIdENABLE_CMD, g_nStringIdERR, g_nStringIdPRED_FINAL, g_nStringIdCOST_MIN};

const CStringDictionary::TStringId FORTE_MPC_LEVEL::scm_anDataOutputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL};

const TDataIOID FORTE_MPC_LEVEL::scm_anEIWith[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 255};
const TForteInt16 FORTE_MPC_LEVEL::scm_anEIWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_MPC_LEVEL::scm_anEventInputNames[] = {g_nStringIdREQ};

const TDataIOID FORTE_MPC_LEVEL::scm_anEOWith[] = {0, 1, 2, 3, 4, 5, 255};
const TForteInt16 FORTE_MPC_LEVEL::scm_anEOWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_MPC_LEVEL::scm_anEventOutputNames[] = {g_nStringIdCNF};


const SFBInterfaceSpec FORTE_MPC_LEVEL::scm_stFBInterfaceSpec = {
  1, scm_anEventInputNames, scm_anEIWith, scm_anEIWithIndexes,
  1, scm_anEventOutputNames, scm_anEOWith, scm_anEOWithIndexes,
  12, scm_anDataInputNames, scm_anDataInputTypeIds,
  6, scm_anDataOutputNames, scm_anDataOutputTypeIds,
  0, nullptr
};

const CStringDictionary::TStringId FORTE_MPC_LEVEL::scm_anInternalsNames[] = {g_nStringIdlast_dac, g_nStringIdbest_dac, g_nStringIdbest_cost, g_nStringIddac_candidate, g_nStringIdy_pred, g_nStringIdpred_error, g_nStringIddelta_dac, g_nStringIdcost, g_nStringIdi, g_nStringIdh};
const CStringDictionary::TStringId FORTE_MPC_LEVEL::scm_anInternalsTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdUINT, g_nStringIdUINT};
const SInternalVarsInformation FORTE_MPC_LEVEL::scm_stInternalVars = {10, scm_anInternalsNames, scm_anInternalsTypeIds};

void FORTE_MPC_LEVEL::setInitialValues() {
}

void FORTE_MPC_LEVEL::alg_ALG_MPC(void) {
  if(st_RESET()) {
  	st_last_dac() = 0.0;
  }
  st_ERR() = SUB(st_SP(), st_PV());
  if((! st_ENABLE())) {
  	st_DAC_OUT() = 0.0;
  	st_MV_PERCENT() = 0.0;
  	st_ENABLE_CMD() = false;
  	st_PRED_FINAL() = st_PV();
  	st_COST_MIN() = 0.0;
  	st_last_dac() = 0.0;
  }
  else {
  	st_best_cost() = 1.0E30;
  	st_best_dac() = st_last_dac();
  	st_PRED_FINAL() = st_PV();
  	if((st_HORIZON() == 0)) {
  		st_h() = 1;
  	}
  	else {
  		st_h() = st_HORIZON();
  	}
  	st_dac_candidate() = st_DAC_MIN();
  	while((st_dac_candidate() <= st_DAC_MAX())) {
  	  st_y_pred() = st_PV();
  	  st_cost() = 0.0;
  	  st_i() = 1;
  	  while((st_i() <= st_h())) {
  	    st_y_pred() = ADD(ADD(MUL(st_A(), st_y_pred()), MUL(st_B(), st_dac_candidate())), st_C());
  	    st_pred_error() = SUB(st_SP(), st_y_pred());
  	    st_cost() = ADD(st_cost(), MUL(st_pred_error(), st_pred_error()));
  	    st_i() = ADD(st_i(), 1);
  	  }
  	  st_delta_dac() = SUB(st_dac_candidate(), st_last_dac());
  	  st_cost() = ADD(st_cost(), MUL(MUL(st_LAMBDA_DU(), st_delta_dac()), st_delta_dac()));
  	  if((st_cost() < st_best_cost())) {
  	  	st_best_cost() = st_cost();
  	  	st_best_dac() = st_dac_candidate();
  	  	st_PRED_FINAL() = st_y_pred();
  	  }
  	  if((st_DAC_STEP() <= 0.0)) {
  	  	st_dac_candidate() = ADD(st_DAC_MAX(), 1.0);
  	  }
  	  else {
  	  	st_dac_candidate() = ADD(st_dac_candidate(), st_DAC_STEP());
  	  }
  	}
  	if((st_best_dac() > st_DAC_MAX())) {
  		st_best_dac() = st_DAC_MAX();
  	}
  	else if((st_best_dac() < st_DAC_MIN())) {
  		st_best_dac() = st_DAC_MIN();
  	}
  	st_DAC_OUT() = st_best_dac();
  	if((st_DAC_MAX() > 0.0)) {
  		st_MV_PERCENT() = MUL(DIV(st_DAC_OUT(), st_DAC_MAX()), 100.0);
  	}
  	else {
  		st_MV_PERCENT() = 0.0;
  	}
  	if((st_DAC_OUT() > 1.0)) {
  		st_ENABLE_CMD() = true;
  	}
  	else {
  		st_ENABLE_CMD() = false;
  	}
  	st_COST_MIN() = st_best_cost();
  	st_last_dac() = st_DAC_OUT();
  }
}


void FORTE_MPC_LEVEL::enterStateSTART(void) {
  m_nECCState = scm_nStateSTART;
}

void FORTE_MPC_LEVEL::enterStateCALC(void) {
  m_nECCState = scm_nStateCALC;
  alg_ALG_MPC();
}

void FORTE_MPC_LEVEL::enterStateDONE(void) {
  m_nECCState = scm_nStateDONE;
  sendOutputEvent(scm_nEventCNFID);
}


void FORTE_MPC_LEVEL::executeEvent(int pa_nEIID){
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


