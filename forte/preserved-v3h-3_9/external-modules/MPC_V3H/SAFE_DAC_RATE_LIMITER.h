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

#ifndef _SAFE_DAC_RATE_LIMITER_H_
#define _SAFE_DAC_RATE_LIMITER_H_

#include "basicfb.h"
#include "forte_bool.h"
#include "forte_lreal.h"
#include "forte_array_at.h"


class FORTE_SAFE_DAC_RATE_LIMITER: public CBasicFB {
  DECLARE_FIRMWARE_FB(FORTE_SAFE_DAC_RATE_LIMITER)

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
  CIEC_LREAL &st_DAC_IN() {
    return *static_cast<CIEC_LREAL*>(getDI(0));
  }
  
  CIEC_LREAL &st_MAX_DELTA_DAC() {
    return *static_cast<CIEC_LREAL*>(getDI(1));
  }
  
  CIEC_LREAL &st_DAC_MIN() {
    return *static_cast<CIEC_LREAL*>(getDI(2));
  }
  
  CIEC_LREAL &st_DAC_MAX() {
    return *static_cast<CIEC_LREAL*>(getDI(3));
  }
  
  CIEC_LREAL &st_INITIAL_DAC() {
    return *static_cast<CIEC_LREAL*>(getDI(4));
  }
  
  CIEC_BOOL &st_RESET() {
    return *static_cast<CIEC_BOOL*>(getDI(5));
  }
  
  CIEC_LREAL &st_DAC_OUT() {
    return *static_cast<CIEC_LREAL*>(getDO(0));
  }
  
  CIEC_BOOL &st_LIMITED() {
    return *static_cast<CIEC_BOOL*>(getDO(1));
  }
  
  CIEC_BOOL &st_INITIALIZED() {
    return *static_cast<CIEC_BOOL*>(getDO(2));
  }
  
  CIEC_BOOL &st_RESET_ACTIVE() {
    return *static_cast<CIEC_BOOL*>(getDO(3));
  }
  
  CIEC_BOOL &st_CONFIGURATION_VALID() {
    return *static_cast<CIEC_BOOL*>(getDO(4));
  }
  
  CIEC_LREAL &st_previous_dac() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(0));
  }
  
  CIEC_BOOL &st_initialized_internal() {
    return *static_cast<CIEC_BOOL*>(getVarInternal(1));
  }
  
  CIEC_LREAL &st_bounded_input() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(2));
  }
  
  CIEC_LREAL &st_bounded_initial() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(3));
  }
  
  CIEC_LREAL &st_delta_dac() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(4));
  }
  
  CIEC_LREAL &st_limited_delta() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(5));
  }
  

  void alg_SAFE_DAC_RATE_LIMITER_ALGORITHM(void);

  static const TForteInt16 scm_nStateSTART = 0;
  static const TForteInt16 scm_nStateCALCULATE = 1;
  static const TForteInt16 scm_nStateCONFIRM = 2;
  
  void enterStateSTART(void);
  void enterStateCALCULATE(void);
  void enterStateCONFIRM(void);

  virtual void executeEvent(int pa_nEIID);

  FORTE_BASIC_FB_DATA_ARRAY(1, 6, 5, 6, 0);

public:
  FORTE_SAFE_DAC_RATE_LIMITER(CStringDictionary::TStringId pa_nInstanceNameId, CResource *pa_poSrcRes) :
      CBasicFB(pa_poSrcRes, &scm_stFBInterfaceSpec, pa_nInstanceNameId, &scm_stInternalVars, m_anFBConnData, m_anFBVarsData) {
  };

  virtual ~FORTE_SAFE_DAC_RATE_LIMITER() = default;
};

#endif // _SAFE_DAC_RATE_LIMITER_H_


