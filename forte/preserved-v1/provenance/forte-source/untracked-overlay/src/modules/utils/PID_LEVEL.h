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

#ifndef _PID_LEVEL_H_
#define _PID_LEVEL_H_

#include "basicfb.h"
#include "forte_bool.h"
#include "forte_lreal.h"
#include "forte_array_at.h"


class FORTE_PID_LEVEL: public CBasicFB {
  DECLARE_FIRMWARE_FB(FORTE_PID_LEVEL)

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
  CIEC_LREAL &st_PV() {
    return *static_cast<CIEC_LREAL*>(getDI(0));
  }
  
  CIEC_LREAL &st_SP() {
    return *static_cast<CIEC_LREAL*>(getDI(1));
  }
  
  CIEC_LREAL &st_KP() {
    return *static_cast<CIEC_LREAL*>(getDI(2));
  }
  
  CIEC_LREAL &st_KI() {
    return *static_cast<CIEC_LREAL*>(getDI(3));
  }
  
  CIEC_LREAL &st_KD() {
    return *static_cast<CIEC_LREAL*>(getDI(4));
  }
  
  CIEC_LREAL &st_TS() {
    return *static_cast<CIEC_LREAL*>(getDI(5));
  }
  
  CIEC_BOOL &st_MANUAL() {
    return *static_cast<CIEC_BOOL*>(getDI(6));
  }
  
  CIEC_LREAL &st_MAN_OUT() {
    return *static_cast<CIEC_LREAL*>(getDI(7));
  }
  
  CIEC_BOOL &st_RESET() {
    return *static_cast<CIEC_BOOL*>(getDI(8));
  }
  
  CIEC_LREAL &st_MV() {
    return *static_cast<CIEC_LREAL*>(getDO(0));
  }
  
  CIEC_LREAL &st_ERR() {
    return *static_cast<CIEC_LREAL*>(getDO(1));
  }
  
  CIEC_LREAL &st_P_TERM() {
    return *static_cast<CIEC_LREAL*>(getDO(2));
  }
  
  CIEC_LREAL &st_I_TERM() {
    return *static_cast<CIEC_LREAL*>(getDO(3));
  }
  
  CIEC_LREAL &st_D_TERM() {
    return *static_cast<CIEC_LREAL*>(getDO(4));
  }
  
  CIEC_LREAL &st_e_prev() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(0));
  }
  
  CIEC_LREAL &st_i_acc() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(1));
  }
  
  CIEC_LREAL &st_u_raw() {
    return *static_cast<CIEC_LREAL*>(getVarInternal(2));
  }
  

  void alg_ALG_PID(void);

  static const TForteInt16 scm_nStateSTART = 0;
  static const TForteInt16 scm_nStateCALC = 1;
  static const TForteInt16 scm_nStateDONE = 2;
  
  void enterStateSTART(void);
  void enterStateCALC(void);
  void enterStateDONE(void);

  virtual void executeEvent(int pa_nEIID);

  FORTE_BASIC_FB_DATA_ARRAY(1, 9, 5, 3, 0);

public:
  FORTE_PID_LEVEL(CStringDictionary::TStringId pa_nInstanceNameId, CResource *pa_poSrcRes) :
      CBasicFB(pa_poSrcRes, &scm_stFBInterfaceSpec, pa_nInstanceNameId, &scm_stInternalVars, m_anFBConnData, m_anFBVarsData) {
  };

  virtual ~FORTE_PID_LEVEL() = default;
};

#endif // _PID_LEVEL_H_


