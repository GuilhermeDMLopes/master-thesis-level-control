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

#ifndef _PI_LEVEL_CONTROLLER_H_
#define _PI_LEVEL_CONTROLLER_H_

#include "basicfb.h"
#include "forte_bool.h"
#include "forte_lreal.h"
#include "forte_array_at.h"


class FORTE_PI_LEVEL_CONTROLLER: public CBasicFB {
  DECLARE_FIRMWARE_FB(FORTE_PI_LEVEL_CONTROLLER)

private:
  static const CStringDictionary::TStringId scm_anDataInputNames[];
  static const CStringDictionary::TStringId scm_anDataInputTypeIds[];
  
  static const CStringDictionary::TStringId scm_anDataOutputNames[];
  static const CStringDictionary::TStringId scm_anDataOutputTypeIds[];
  
  static const TEventID scm_nEventREQID = 0;
  
   static const TDataIOID scm_anEIWith[];
  static const TForteInt16 scm_anEIWithIndexes[];
  static const CStringDictionary::TStringId scm_anEventInputNames[];
  
  static const TEventID scm_nEventCNFID = 0;
  
   static const TDataIOID scm_anEOWith[]; 
  static const TForteInt16 scm_anEOWithIndexes[];
  static const CStringDictionary::TStringId scm_anEventOutputNames[];
  

  static const SFBInterfaceSpec scm_stFBInterfaceSpec;

static const CStringDictionary::TStringId scm_anInternalsNames[];
static const CStringDictionary::TStringId scm_anInternalsTypeIds[];
static const SInternalVarsInformation scm_stInternalVars;
virtual void setInitialValues();
  CIEC_LREAL &st_PROCESS_VARIABLE() {
    return *static_cast<CIEC_LREAL*>(getDI(0));
  }
  
  CIEC_LREAL &st_SETPOINT() {
    return *static_cast<CIEC_LREAL*>(getDI(1));
  }
  
  CIEC_LREAL &st_PROPORTIONAL_GAIN() {
    return *static_cast<CIEC_LREAL*>(getDI(2));
  }
  
  CIEC_LREAL &st_INTEGRAL_GAIN() {
    return *static_cast<CIEC_LREAL*>(getDI(3));
  }
  
  CIEC_LREAL &st_SAMPLING_TIME_S() {
    return *static_cast<CIEC_LREAL*>(getDI(4));
  }
  
  CIEC_LREAL &st_OUTPUT_MIN() {
    return *static_cast<CIEC_LREAL*>(getDI(5));
  }
  
  CIEC_LREAL &st_OUTPUT_MAX() {
    return *static_cast<CIEC_LREAL*>(getDI(6));
  }
  
  CIEC_BOOL &st_MANUAL() {
    return *static_cast<CIEC_BOOL*>(getDI(7));
  }
  
  CIEC_LREAL &st_MANUAL_OUTPUT() {
    return *static_cast<CIEC_LREAL*>(getDI(8));
  }
  
  CIEC_BOOL &st_RESET() {
    return *static_cast<CIEC_BOOL*>(getDI(9));
  }
  
  CIEC_LREAL &st_OUTPUT() {
    return *static_cast<CIEC_LREAL*>(getDO(0));
  }
  
  CIEC_LREAL &st_ERROR() {
    return *static_cast<CIEC_LREAL*>(getDO(1));
  }
  
  CIEC_LREAL &st_PROPORTIONAL_TERM() {
    return *static_cast<CIEC_LREAL*>(getDO(2));
  }
  
  CIEC_LREAL &st_INTEGRAL_TERM() {
    return *static_cast<CIEC_LREAL*>(getDO(3));
  }
  
  CIEC_LREAL &st_UNSATURATED_OUTPUT() {
    return *static_cast<CIEC_LREAL*>(getDO(4));
  }
  
  CIEC_BOOL &st_SATURATED() {
    return *static_cast<CIEC_BOOL*>(getDO(5));
  }
  
  CIEC_BOOL &st_MANUAL_ACTIVE() {
    return *static_cast<CIEC_BOOL*>(getDO(6));
  }
  
  CIEC_BOOL &st_RESET_ACTIVE() {
    return *static_cast<CIEC_BOOL*>(getDO(7));
  }
  
  CIEC_BOOL &st_CONFIGURATION_VALID() {
    return *static_cast<CIEC_BOOL*>(getDO(8));
  }
  
  CIEC_LREAL &st_integral_term_internal() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(0));
  }
  
  CIEC_BOOL &st_manual_was_active() {
    return *static_cast<CIEC_BOOL*>(getVarInternal(1));
  }
  
  CIEC_LREAL &st_integral_increment() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(2));
  }
  
  CIEC_LREAL &st_candidate_integral() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(3));
  }
  
  CIEC_LREAL &st_candidate_unsaturated_output() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(4));
  }
  
  CIEC_LREAL &st_clamped_manual_output() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(5));
  }
  

  void alg_PI_CONTROL_ALGORITHM(void);

  static const TForteInt16 scm_nStateSTART = 0;
  static const TForteInt16 scm_nStateCALCULATE = 1;
  static const TForteInt16 scm_nStateCONFIRM = 2;
  
  void enterStateSTART(void);
  void enterStateCALCULATE(void);
  void enterStateCONFIRM(void);

  virtual void executeEvent(int pa_nEIID);

  FORTE_BASIC_FB_DATA_ARRAY(1, 10, 9, 6, 0);

public:
  FORTE_PI_LEVEL_CONTROLLER(CStringDictionary::TStringId pa_nInstanceNameId, CResource *pa_poSrcRes) :
      CBasicFB(pa_poSrcRes, &scm_stFBInterfaceSpec, pa_nInstanceNameId, &scm_stInternalVars, m_anFBConnData, m_anFBVarsData) {
  };

  virtual ~FORTE_PI_LEVEL_CONTROLLER() = default;
};

#endif // _PI_LEVEL_CONTROLLER_H_


