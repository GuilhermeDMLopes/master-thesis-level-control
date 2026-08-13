/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: PI_LEVEL_CONTROLLER
 *** Description: PI level controller with anti-windup, manual tracking, and diagnostics
 *** Version:
***     1.0: 2026-07-24/Guilherme -  - 
 *************************************************************************/

#include "PI_LEVEL_CONTROLLER.h"
#ifdef FORTE_ENABLE_GENERATED_SOURCE_CPP
#include "PI_LEVEL_CONTROLLER_gen.cpp"
#endif


DEFINE_FIRMWARE_FB(FORTE_PI_LEVEL_CONTROLLER, g_nStringIdPI_LEVEL_CONTROLLER)

const CStringDictionary::TStringId FORTE_PI_LEVEL_CONTROLLER::scm_anDataInputNames[] = {g_nStringIdPROCESS_VARIABLE, g_nStringIdSETPOINT, g_nStringIdPROPORTIONAL_GAIN, g_nStringIdINTEGRAL_GAIN, g_nStringIdSAMPLING_TIME_S, g_nStringIdOUTPUT_MIN, g_nStringIdOUTPUT_MAX, g_nStringIdMANUAL, g_nStringIdMANUAL_OUTPUT, g_nStringIdRESET};

const CStringDictionary::TStringId FORTE_PI_LEVEL_CONTROLLER::scm_anDataInputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdBOOL};

const CStringDictionary::TStringId FORTE_PI_LEVEL_CONTROLLER::scm_anDataOutputNames[] = {g_nStringIdOUTPUT, g_nStringIdERROR, g_nStringIdPROPORTIONAL_TERM, g_nStringIdINTEGRAL_TERM, g_nStringIdUNSATURATED_OUTPUT, g_nStringIdSATURATED, g_nStringIdMANUAL_ACTIVE, g_nStringIdRESET_ACTIVE, g_nStringIdCONFIGURATION_VALID};

const CStringDictionary::TStringId FORTE_PI_LEVEL_CONTROLLER::scm_anDataOutputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdBOOL, g_nStringIdBOOL, g_nStringIdBOOL};

const TDataIOID FORTE_PI_LEVEL_CONTROLLER::scm_anEIWith[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 255};
const TForteInt16 FORTE_PI_LEVEL_CONTROLLER::scm_anEIWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_PI_LEVEL_CONTROLLER::scm_anEventInputNames[] = {g_nStringIdREQ};

const TDataIOID FORTE_PI_LEVEL_CONTROLLER::scm_anEOWith[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 255};
const TForteInt16 FORTE_PI_LEVEL_CONTROLLER::scm_anEOWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_PI_LEVEL_CONTROLLER::scm_anEventOutputNames[] = {g_nStringIdCNF};


const SFBInterfaceSpec FORTE_PI_LEVEL_CONTROLLER::scm_stFBInterfaceSpec = {
  1, scm_anEventInputNames, scm_anEIWith, scm_anEIWithIndexes,
  1, scm_anEventOutputNames, scm_anEOWith, scm_anEOWithIndexes,
  10, scm_anDataInputNames, scm_anDataInputTypeIds,
  9, scm_anDataOutputNames, scm_anDataOutputTypeIds,
  0, nullptr
};

const CStringDictionary::TStringId FORTE_PI_LEVEL_CONTROLLER::scm_anInternalsNames[] = {g_nStringIdintegral_term_internal, g_nStringIdmanual_was_active, g_nStringIdintegral_increment, g_nStringIdcandidate_integral, g_nStringIdcandidate_unsaturated_output, g_nStringIdclamped_manual_output};
const CStringDictionary::TStringId FORTE_PI_LEVEL_CONTROLLER::scm_anInternalsTypeIds[] = {g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL};
const SInternalVarsInformation FORTE_PI_LEVEL_CONTROLLER::scm_stInternalVars = {6, scm_anInternalsNames, scm_anInternalsTypeIds};

void FORTE_PI_LEVEL_CONTROLLER::setInitialValues() {
  st_integral_term_internal() = 0.0;
  st_manual_was_active() = false;
  st_integral_increment() = 0.0;
  st_candidate_integral() = 0.0;
  st_candidate_unsaturated_output() = 0.0;
  st_clamped_manual_output() = 0.0;
}

void FORTE_PI_LEVEL_CONTROLLER::alg_PI_CONTROL_ALGORITHM(void) {
  st_ERROR() = SUB(st_SETPOINT(), st_PROCESS_VARIABLE());
  st_PROPORTIONAL_TERM() = MUL(st_PROPORTIONAL_GAIN(), st_ERROR());
  st_CONFIGURATION_VALID() = ((st_SAMPLING_TIME_S() > 0.0) && (st_OUTPUT_MIN() < st_OUTPUT_MAX()));
  if((! st_CONFIGURATION_VALID())) {
  	st_integral_term_internal() = 0.0;
  	st_manual_was_active() = false;
  	st_OUTPUT() = 0.0;
  	st_INTEGRAL_TERM() = 0.0;
  	st_UNSATURATED_OUTPUT() = 0.0;
  	st_SATURATED() = false;
  	st_MANUAL_ACTIVE() = false;
  	st_RESET_ACTIVE() = false;
  }
  else if(st_RESET()) {
  	st_integral_term_internal() = 0.0;
  	st_manual_was_active() = false;
  	st_OUTPUT() = 0.0;
  	if((st_OUTPUT() > st_OUTPUT_MAX())) {
  		st_OUTPUT() = st_OUTPUT_MAX();
  	}
  	else if((st_OUTPUT() < st_OUTPUT_MIN())) {
  		st_OUTPUT() = st_OUTPUT_MIN();
  	}
  	st_INTEGRAL_TERM() = 0.0;
  	st_UNSATURATED_OUTPUT() = st_OUTPUT();
  	st_SATURATED() = false;
  	st_MANUAL_ACTIVE() = st_MANUAL();
  	st_RESET_ACTIVE() = true;
  }
  else if(st_MANUAL()) {
  	st_clamped_manual_output() = st_MANUAL_OUTPUT();
  	if((st_clamped_manual_output() > st_OUTPUT_MAX())) {
  		st_clamped_manual_output() = st_OUTPUT_MAX();
  	}
  	else if((st_clamped_manual_output() < st_OUTPUT_MIN())) {
  		st_clamped_manual_output() = st_OUTPUT_MIN();
  	}
  	st_OUTPUT() = st_clamped_manual_output();
  	st_integral_term_internal() = SUB(st_OUTPUT(), st_PROPORTIONAL_TERM());
  	st_INTEGRAL_TERM() = st_integral_term_internal();
  	st_UNSATURATED_OUTPUT() = st_OUTPUT();
  	st_SATURATED() = (st_OUTPUT() != st_MANUAL_OUTPUT());
  	st_MANUAL_ACTIVE() = true;
  	st_RESET_ACTIVE() = false;
  	st_manual_was_active() = true;
  }
  else {
  	if(st_manual_was_active()) {
  		st_manual_was_active() = false;
  	}
  	else {
  		st_integral_increment() = MUL(MUL(st_INTEGRAL_GAIN(), st_ERROR()), st_SAMPLING_TIME_S());
  		st_candidate_integral() = ADD(st_integral_term_internal(), st_integral_increment());
  		st_candidate_unsaturated_output() = ADD(st_PROPORTIONAL_TERM(), st_candidate_integral());
  		if((! (((st_candidate_unsaturated_output() > st_OUTPUT_MAX()) && (st_integral_increment() > 0.0)) || ((st_candidate_unsaturated_output() < st_OUTPUT_MIN()) && (st_integral_increment() < 0.0))))) {
  			st_integral_term_internal() = st_candidate_integral();
  		}
  	}
  	st_INTEGRAL_TERM() = st_integral_term_internal();
  	st_UNSATURATED_OUTPUT() = ADD(st_PROPORTIONAL_TERM(), st_INTEGRAL_TERM());
  	st_OUTPUT() = st_UNSATURATED_OUTPUT();
  	if((st_OUTPUT() > st_OUTPUT_MAX())) {
  		st_OUTPUT() = st_OUTPUT_MAX();
  	}
  	else if((st_OUTPUT() < st_OUTPUT_MIN())) {
  		st_OUTPUT() = st_OUTPUT_MIN();
  	}
  	st_SATURATED() = (st_OUTPUT() != st_UNSATURATED_OUTPUT());
  	st_MANUAL_ACTIVE() = false;
  	st_RESET_ACTIVE() = false;
  }
}


void FORTE_PI_LEVEL_CONTROLLER::enterStateSTART(void) {
  m_nECCState = scm_nStateSTART;
}

void FORTE_PI_LEVEL_CONTROLLER::enterStateCALCULATE(void) {
  m_nECCState = scm_nStateCALCULATE;
  alg_PI_CONTROL_ALGORITHM();
}

void FORTE_PI_LEVEL_CONTROLLER::enterStateCONFIRM(void) {
  m_nECCState = scm_nStateCONFIRM;
  sendOutputEvent(scm_nEventCNFID);
}


void FORTE_PI_LEVEL_CONTROLLER::executeEvent(int pa_nEIID){
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


