/*
Copyright 2011 Acknack Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
var reloadPage = undefined;

(function($) {
	
	var clickedButton = undefined;
	var dialogOpen = false;
	var viewerSession = undefined;
	
	/**
	* Final variables
	*/
	var BLIP_ID_PREFIX = {
	    CHILDREN_CONTAINER  :   'blip-children-container-', 
		CONTAINER	    	:	'blip-container-',
		INLINE_CONTAINER    :   'inline-container-',
		INLINE_TOGGLE       :   'inline-toggle-',
		CONTRIBUTOR		    :	'blip-contributor-',
		LAST_EDITED		    :	'blip-last-edited-',
		CONTENT			    :	'blip-content-',
		REPLY			    :	'reply-button-',
		REPLY_IMAGE         :   "reply-image-", 
		WORKING			    :	'working-image-',
		READ_STATUS		    :	'blip-readstatus'
	};
	var PROFILE_ID_PREFIX = {
		IMG				    :	'participantImage_'	
	};
	
	/**
	* Represnts participant profiles in javascript way
	* @param rawParticipants: the raw participants json
	*/
	var Profiles = function(rawProfiles) {
	    var self = this;
	    self.rawProfiles = rawProfiles;
	    
	    /**
	    * @param id: the participants wave user id
	    * @return the participant json object
	    */
	    self.getRawParticipant = function(id) {
	        return self.rawProfiles[id] || {};
	    };
	    
	    /**
	    * @param id: the participants wave user id
	    * @return the participants friendly name or the given address if not known
	    */
	    self.getDisplayName = function(id) {
	        if(id === robotEmail) {
				return "Mr-Ray";	
			} else if (id.indexOf(robotIdent + "+") === 0 && id.indexOf(publicEmail.replace("@", proxyForAtReplace)) !== -1){
			    return id.replace(robotIdent + "+", "").replace("." + publicEmail.replace("@", proxyForAtReplace), "").replace("@" + robotDomain, "") + "(via Mr-Ray Public)";
		    } else if(id.indexOf(robotIdent + "+") === 0 && id.indexOf("@" + robotDomain === id.length - 12)) {
				return utils.maskEmailIfPublic(id.replace(robotIdent + "+", "").replace("@" + robotDomain, "").replace(proxyForAtReplace, "@")) + "(via Mr-Ray)";
			} else {
			    return self.getRawParticipant(id)['displayName'] || id;
		    }
	    };
	    
	    /**
	    * @param id: the participants wave user id
	    * @return the participants avatar url or a default image if not known
	    */
	    self.getImageUrl = function(id) {
	        if(id === robotEmail) {
				return robotWebAddress + "web/media/icon.png";
			} else if (id.indexOf(robotIdent + "+") === 0 && id.indexOf(publicEmail.replace("@", proxyForAtReplace)) !== -1){
    		    return robotWebAddress + "web/media/icon_public.png";
    		}else if(id.indexOf(robotIdent + "+") === 0 && id.indexOf("@" + robotDomain) === id.length - 12) {
				return robotWebAddress + "web/media/icon_proxyfor.png";
			} else {
			    return self.getRawParticipant(id)['thumbUrl'] || robotWebAddress + "web/media/icon_waver.png";
			}
	    };
	};
	
	/**
	* Models this users current session including unread counts, permissions etc
	* @param isPublic: dictates if this is a public wave or not
	* @param rawRwPermission: the read-write permission sent from the server
	*/
	var Session = function(rawIsPublic, rawRwPermission) {
	    var self = this;
	    self.rawIsPublic = rawIsPublic;
	    self.rawRwPermission = rawRwPermission;
	    self.unreadCount = 0;
	    
	    /**
	    * @return True if this session is public
	    */
	    self.isPublic = function() {
	        return self.rawIsPublic;
	    };
	    
	    /**
	    * @return True if this session is editable
	    */
	    self.canWrite = function() {
	        if (self.rawRwPermission === "rw") {
	            return true;
	        } else {
	            return false;
            }
	    };
	    
	    /**
	    * @param qty: the amount to increment the unread count by
	    */
	    self.incrementUnreadCount = function(qty) {
	        self.unreadCount += qty;
	    };
	    
	    /**
	    * @param qty: the amount to decrement the unread count by
	    */
	    self.decrementUnreadCount = function(qty) {
	        self.unreadCount -= qty
	    }
	    
	    /**
	    * @return the unread count
	    */
	    self.getUnreadCount = function() {
	        return self.unreadCount;
	    }
	};
	
	/**
	* General utils used through code
	*/
	var utils = {
		/**
		* Converts an epoch string to a formatted date string
		* @param epoch: the epoch date number
		* @return a string representing the date dd-mm-yyyy
		*/
		epochToDate				:	function(epoch) {
			var d = new Date(epoch);
			var day = d.getDate();
			var month = d.getMonth() + 1;
			var year = d.getFullYear();
			
			if(month < 10) {
				month = "0" + month;	
			}
			
			return day + "-" + month + "-" + year;
		},
		/**
		* Converts an epoch string to a formatted date and time string
		* @param epoch: the epoch date number
		* @return a string representing the date and time hh:mm dd-mm-yyyy
		*/
		epochToDateTime			:	function(epoch) {
			var d = new Date(epoch);
			var hours = d.getHours();
			var minutes = d.getMinutes();
			var day = d.getDate();
			var month = d.getMonth() + 1;
			var year = d.getFullYear();
			
			if(minutes < 10) {
				minutes = "0" + minutes;	
			}
			if(month < 10) {
				month = "0" + month;	
			}
			
			return hours + ":" + minutes + " " + day + "-" + month + "-" + year;
		},
		/**
		* Converts an array of participants to a string of participants (String is shortened)
		* @param profiles: a Profiles object modelling profiles
		* @param participants: array of participants
		* @param maxLength: the maximum length of the string. Submit 0 to not cut
		* @return a string of participants that is shortened to a maximum length
		*/
		participantsToString	:	function(profiles, participants, maxLength) {
			var participantString = "";
			//Add participants together
			for(var i = 0; i < participants.length; i++) {
				if(i === participants.length -1) {
					participantString += profiles.getDisplayName(participants[i]);
				} else {
					participantString += profiles.getDisplayName(participants[i]) + ", ";
				}	
			}
			
			//Shorten & return
			if(maxLength !== 0) {
				if(participantString.length > maxLength) {
					return participantString.substring(0, maxLength-3) + "...";	
				}
			}
			return participantString;
		},
		/**
		* Returns a string containing the participants uid and display name
		* @param profiles: a Participants object modelling profiles
		* @param id: the participant profile
		* @return displayName (id)
		*/
		getParticipantDisplayNameAndRaw    :    function(profiles, id) {
		    return profiles.getDisplayName(id) + " (" + utils.maskEmailIfPublic(id) + ")";
		},
		/**
		* Fetches arguments from a url string
		* @param key: the name of the argument
		* @return the value or an empty string if it does not exist
		*/
		getUrlArg				:	function(key) {
			key = key.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
			var regexS = "[\\?&]" + key + "=([^&#]*)";
  			var regex = new RegExp( regexS );
  			var results = regex.exec( window.location.href );
  			if( results == null ) {
    			return "";
  			} else {
    			return results[1];
  			}
		},
		/**
		* Returns a friendly version of the unread count
		* @return the unread count in brackets with an upper and lower limit
		*/
		getFriendlyUnreadCount  :    function() {
		    var count = viewerSession.getUnreadCount();
		    if(count === 0) {
		        return "";
		    } else if(count >= 100) {
		        return "(99+) ";
		    } else {
		        return " (" + count + ")";
		    }
		},
		/**
		* Masks an email address if the session is public
		* @param email: the email address to mask
		* @return username@****.com
		*/
		maskEmailIfPublic   :       function(email) {
		    if(viewerSession.isPublic()) {
		        maskedEmail = email;
		        
		        //Replace the @***whatever***.com
		        atIndex = maskedEmail.lastIndexOf("@");
		        dotIndex = maskedEmail.lastIndexOf(".");
		        if (atIndex !== -1 && dotIndex !== -1) {
		            maskedEmail = maskedEmail.substr(0, atIndex + 1) + '******' + maskedEmail.substr(dotIndex);
	            }
	            
	            //Replace the -_at_-***whatever***.com
	            atIndex = maskedEmail.indexOf(proxyForAtReplace);
	            if(atIndex !== -1) {
	                dotIndex = maskedEmail.substr(atIndex, maskedEmail.length).indexOf(".") + atIndex;
	                maskedEmail = maskedEmail.substr(0, atIndex) + '@******' + maskedEmail.substr(dotIndex);
	            }
	            email = maskedEmail;
		    }
		    return email;
		},
		/**
		* Inserts a new string into an existing string at the given positin
		* @param originalString: the existing string to insert into
		* @param toInsert: the string to insert into the existing one
		* @param index: the index to insert the new string
		* @return: the new concatinated string
		*/
		insertIntoString    :   function(originalString, toInsert, index) {
		    return originalString.substr(0, index) + toInsert + originalString.substr(index);
		},
		/**
		* @return true if waveletJson's are the same
		*/
		areWaveletsSame     :   function(wavelet1, wavelet2) {
		    if(JSON.stringify(wavelet1) === JSON.stringify(wavelet2)) {
		        return true;
		    }
		    return false;
		}
	};
	
	/**
	* Sets a blip as being read
	* @param blipId: the blip id to mark read
	* @param waveTitle: the wave title
	*/
	var setBlipAsRead = function(blipId, waveTitle) {
		//var divId = $(button).attr("id");
		//var blipId = divId.replace(BLIP_ID_PREFIX['CONTAINER'], "");
		var readStatusElem = $(document.getElementById(BLIP_ID_PREFIX['READ_STATUS'] + blipId));
		
		if(readStatusElem.attr("class").indexOf("blipIsRead") === -1) {
			//Fade the element for immediate update
			readStatusElem.fadeOut('slow', function() {$(this).attr("style", "visibility: hidden;")});
			readStatusElem.attr("class", readStatusElem.attr("class") + " blipIsRead");
			//Update the title read count
			viewerSession.decrementUnreadCount(1);
			$(document).attr("title", waveTitle + utils.getFriendlyUnreadCount() + " - Mr-Ray. Wav-e-mail");
			
			//Update the server
			var jsondata = JSON.stringify({	'action': 'READ',
	     									'blipid': blipId,
	     									'waveid': utils.getUrlArg('waveid'),
	     									'waveletid': utils.getUrlArg('waveletid'),
	     									'email': utils.getUrlArg('email'),
	     									'auth': utils.getUrlArg('auth')})
	     			
			$.ajax({
	     		'dataType': 'json',
	     		'url': robotWebAddress + "wave/action/",
	     		'type': 'POST',
	     		'contentType': 'application/json',
	     		'data': jsondata
	   		});
		}
	};
	
	/**
	* Used for generating elements convieniently
	* @param elemType: the element type e.g. 'div'
	* @param attr: map containing attributes e.g. {'id': 'myid'}
	* @param elemText: the text to place in the element. false for none
	* @param clickEvent: the event to call when the element is clicked. false for none
	* @return the element
	*/
	var elementFactory = function(elemType, attr, elemText, clickEvent) {
		var elem = $(document.createElement(elemType));
		for(var n in attr) {
			elem.attr(n, attr[n]);	
		}
		if(elemText !== undefined && elemText !== false) {
			elem.text(elemText);	
		}
		if(clickEvent !== undefined && clickEvent !== false) {
			elem.click(clickEvent);	
		}
		return elem;
	};
	
	/**
	* Represents an element in a javascript way
	* @param key: the key that returned this raw element
	* @param rawElement: the raw element json
	*/
	var Element = function(key, rawElement) {
	    var self = this;
	    self.position = key;
	    self.rawElement = rawElement;
	    self.type = rawElement['type'];
	    
	    /**
	    * @return all the properties in their raw json object or undefined if not found
	    */
	    self.getProperties = function() {
	        return self.rawElement['properties'] || undefined;
	    };
	    
	    /**
	    * @return the different properties owned by this element
	    */
	    self.getPropertyKeys = function() {
	        var keys = [];
	        for(var k in self.getProperties()) {
	            keys.push(k);
	        }
	        return keys;
	    };
	    
	    /**
	    * @param key: the property to fetch
	    * @return the properties value or undefined if not found
	    */
	    self.getProperty = function(key) {
	        var properties = self.getProperties();
	        if(properties === undefined) {
	            return undefined;
	        }
	        return properties[key];
	    };
	    
	    /**
	    * Returns the classes that need to be applied to this item so it is
	    * styled correctly.
	    * @return a string of all the classes for this element
	    */
	    self.getClasses = function() {
	        if(self.type === "LINE") {
	            var lineType = self.getProperty('lineType');
	            if(lineType !== undefined) {
	                return "blip-text-" + lineType;
	            }
            }
	        return "";
	    };
	    
	    /**
	    * Returns the styles that need to be applied to this item so it is
	    * displayed correctly.
	    * @return a string of all styles for this element
	    */
	    self.getStyles = function() {
	        var style = "";
	        if(self.type === "LINE") {
	            var indent = self.getProperty('indent');
	            if(indent !== undefined) {
	                style += "margin-left: " + (14*indent) + "px;";
	            }
	            
	            var alignment = self.getProperty('alignment');
	            if(alignment !== undefined) {
	                if(alignment === "l") {
	                    style +="text-align: left;"
	                } else if(alignment === "c") {
	                    style +="text-align: center;"
	                } else if(alignment === "r") {
	                    style +="text-align: right;"
	                }
	            }
            }
            return style;
	    };
	};
	
	/**
	* Represents a blip in javascript way
	* @param profiles: the Profiles object containing data about participants
	* @param rawBlip: the raw data structure representing the blip
	* @param wavelet: the parent wavelet
	* @param isRead: True or False dictating if the user has read the blip
	*/
	var Blip = function(profiles, rawBlip, wavelet, isRead) {
		//Extract properties
		var self = this;
		self.profiles = profiles;
		self.blipId = rawBlip['blipId'];
		self.waveletId = rawBlip['waveletId'];
		self.waveId = rawBlip['waveId'];
		self.rawElements = rawBlip['elements'];
		self.contributors = rawBlip['contributors'];
		self.creator = rawBlip['creator'];
		self.rawAnnotations = rawBlip['annotations'];
		self.rawContent = rawBlip['content'];
		self.childBlipIds = rawBlip['childBlipIds'];
		self.version = rawBlip['version'];
		self.lastModifiedTime = rawBlip['lastModifiedTime'];
		self.parentBlipId = rawBlip['parentBlipId'];
		self.wavelet = wavelet;
		self.isRead = isRead;
		self._isInline = undefined;
		self._inlinePosition = undefined;
		
		/**
		* Returns the text
		* @return blip text
		*/
		self.getText = function() {
			return self.rawContent;	
		};
		
		/**
		* Returns true if the blip is root
		* @return true if the blip is root, false if now
		*/
		self.isRoot = function() {
			if(self.parentBlipId === null) {
				return true;	
			}
			return false;
		};
		
		
		/**
		* Renders the text correctly using html elements
		* @param containerElem: the element that should contain the text
		*/
		self.renderText = function(containerElem) {
		    var rawText = self.getText();
		    var elements = self.getElements(null);
		    //Fetch the keys from the element map
		    var indicies = [];
		    for(var k in elements) {
		        indicies.push(k);
		    }
		    indicies = indicies.sort(function(a,b){return b-a});
		    
		    //Create html elements for each element
		    var endIndex = rawText.length;
		    for(var i=0; i< indicies.length; i++) {
			    var index = indicies[i];
			    var element = elements[index];

			    if(element.type === "LINE") {
			        containerElem.prepend(elementFactory("p",
			        {
			            "class" : element.getClasses(),
			            "style" : element.getStyles()
			        },
			        rawText.substr(index, endIndex-index),
			        false));
			    } else if(element.type === "INLINE_BLIP") {
			        containerElem.prepend(elementFactory("p",
			        {
			            "class" : element.getClasses(),
			            "style" : element.getStyles()
			        },
			        rawText.substr(index, endIndex-index),
			        false));
			        containerElem.prepend(elementFactory("div",
			        {
			            "id"    : BLIP_ID_PREFIX['INLINE_CONTAINER'] + element.getProperty("id"),
			            "style" : "width: 100%;"
			        },
			        false,
			        false));
			        containerElem.prepend(elementFactory("img",
			        {
			            "src"   : "http://mr-ray.appspot.com/web/media/inline.png",
			            "class" : "inline-identifier"
			        },
			        false,
			        false));
			    } else if(element.type === "GADGET") {
			        containerElem.prepend(elementFactory("p",
			        {
			            "class" : element.getClasses(),
			            "style" : element.getStyles()
			        },
			        rawText.substr(index, endIndex-index),
			        false));
			        var gadgetContainer = elementFactory("div",
			        {
			            "class" : "gadget-container"
			        },
			        false,
			        false);
			        containerElem.prepend(gadgetContainer);
			        gadgetContainer.append(elementFactory("img",
			        {
			            "src"   : "http://mr-ray.appspot.com/web/media/gadgetholder.png"
			        },
			        false,
			        false));
			        gadgetContainer.append(elementFactory("p", {}, "Gadget support available in an upcoming release", false));
			    }
			    endIndex = index;
			}
			
			//Set the root blip to be bold
			if(self.isRoot()) {
			    var rootBlipTitle = $(containerElem.children().get(0));
			    rootBlipTitle.attr("style", rootBlipTitle.attr("style")+ " font-weight:bold;")
			}
		}
		
		/**
		* Returns the parent blip
		* @return the parent blip or undefined if none
		*/
		self.getParentBlip = function() {
			if(self.parentBlipId === undefined) {
				return undefined;	
			}
			return self.wavelet.getBlip(self.parentBlipId);
		};
		
		/**
		* Returns child blips
		* @return an array of child blips
		*/
		self.getChildBlips = function() {
			var childBlips = [];
			for (id in self.childBlipIds) {
				childBlips.push(self.wavelet.getBlip(self.childBlipIds[id]));	
			}
			return childBlips;
		};
		
		/**
		* @param type: the type you want returned or null if all
		* @Return all elements of provided type keyed by their position in the blip
		*/
		self.getElements = function(type) {
		    var elements = {};
		    if(type === null) {
		        for(var key in self.rawElements) {
		            elements[key] = new Element(key, self.rawElements[key]);
    		    }
	        } else {
	            for(var key in self.rawElements) {
	                var element = new Element(key, self.rawElements[key]);
	                if (element.type === type) {
	                    elements[key] = element;
	                }
    		    }
	        }
	        return elements;
		};
		
		/**
		* Caches the result in the object so consecutive calls are more efficient
		* @return the index where this blip appears in the parent blip or 
		*           undefined if it is not inline
		*/
		self._getInlinePosition = function() {
		    if(self._isInline !== undefined) {
		        return self._inlinePosition;
		    }
		    var parent = self.getParentBlip();
		    if (parent === undefined) {
		        self._isInline = false;
		        return undefined;
		    }
		    var parentInlineBlipElements = parent.getElements("INLINE_BLIP");
		    for(var key in parentInlineBlipElements) {		    
		        var element = parentInlineBlipElements[key];
		        if(element.getProperty('id') === self.blipId) {
		            //We can assume this blip will only be inline in one parent
		            self._isInline = true;
		            self._inlinePosition = element.position;
		            return element.position;
		        }
		    }
		    self.isInline = false;
		    return undefined;
		};
		
		/**
		* @return true if this blip is inline
		*/
		self.isInline = function() {
		    if(self._getInlinePosition() === undefined) {
		        return false;
		    } else {
		        return true;
		    }
		};
		
		/**
		* @return the position where this blip appears in the parent or 
		*        undefined if it does not
		*/
		self.inlinePosition = function() {
		    return self._getInlinePosition();
		};
		
		/**
		* Renders the blip appending the content to the provided element
		* @param parentDivElem: the element to append the new blip too
		* @param isSubReply: if this blip is a sub reply set to true
		* @return the blip structure element
		*/
		self.render = function(parentDivElem, isSubReply) {
			//**************Container element**************
			//Handles all indentation etc
			var blipStructureSettings = {'id'	:	BLIP_ID_PREFIX['CHILDREN_CONTAINER'] + self.blipId}
			if(isSubReply) {
				blipStructureSettings['class'] = 'subreply';
			}
			var blipStructure = elementFactory("div", blipStructureSettings, false, false);
			parentDivElem.append(blipStructure);
			
			//Changes the mark read handler depending on permissions
			var markReadHandler = function(){setBlipAsRead($(this).attr("id").replace(BLIP_ID_PREFIX['CONTAINER'], ""), wavelet.title)};
			if(viewerSession.isPublic()) {
			    markReadHandler = false;
			}
			
			var blipContainer = elementFactory(
					"div",
					{
						'id'	:	BLIP_ID_PREFIX['CONTAINER'] + self.blipId,
						'class'	:	'blipcontainer'
					},
					false,
					markReadHandler
				);
			blipStructure.append(blipContainer);
			
			//**************Table to contain visible elements**************
			var blipTable = elementFactory(
				"table", 
				{
					'class'		:	'bliptable'	
				},
				false,
				false);
			blipContainer.append(blipTable);
			
			//**************Table rows**************
			var blipTableTopRow = elementFactory("tr", {}, false, false);
			blipTable.append(blipTableTopRow);
			
			var blipTableBottomRow = elementFactory("tr", {}, false, false);
			blipTable.append(blipTableBottomRow);
			
			//**************Read status**************
			var readStatus = elementFactory(
				"td",
				{
					"rowspan"	:	"2",
					"class"		:	"readstatus",
					"id"		:	BLIP_ID_PREFIX['READ_STATUS'] + self.blipId
				},
				false,
				false
			);
			if(self.isRead || viewerSession.isPublic()) {
				readStatus.attr("style", "visibility: hidden;");
				readStatus.attr("class", readStatus.attr("class") + " blipIsRead");
			} else {
			    viewerSession.incrementUnreadCount(1);
			}
			blipTableTopRow.append(readStatus);
			readStatus.append($(document.createTextNode('\u00a0')));//Fixes ie bug
			
			//**************Actions**************
			if(viewerSession.canWrite()) {
			    var actionCell = elementFactory("td",
    		    {
    		        "rowspan" : "2"
    		    }, false, false);
    		    blipTableTopRow.append(actionCell);
    		    
			    var replyButton = elementFactory("button",
			    {
			        "id"    : BLIP_ID_PREFIX['REPLY'] + self.blipId,
			        "class" : "ui-state-default ui-corner-all reply-button"
			    },
			    "reply",
			    function() {
    			    clickedButton = this;
					dialogOpen = true;
					if(viewerSession.isPublic() === false){
					    setBlipAsRead($(this).attr("id").replace(BLIP_ID_PREFIX['REPLY'], ""), wavelet.title);
					}
					
					$('#replyform').dialog('open');
					if(viewerSession.isPublic()) {
					    if($('#responderName').val() === ""){
					        $('#responderName').focus();
					    } else {
					        $('#response').focus();
					    }
					} else {
					    $('#response').focus();
					}
					return false;
    			});
			    actionCell.append(replyButton);
			    replyButton.hover(
                    function(){ 
                    	$(this).addClass("ui-state-hover"); 
                    },
                    function(){ 
                    	$(this).removeClass("ui-state-hover"); 
                    }
                );
		    }
			
			//**************Contributors**************
			var contributors = elementFactory(
				"td",
				{
					"id"		:	BLIP_ID_PREFIX['CONTRIBUTOR'] + self.blipId,
					"class"		:	"blipcontributors",
					"title"		:	utils.participantsToString(self.profiles, self.contributors, 0)
				},
				utils.participantsToString(self.profiles, self.contributors, 50),
				false
			);
			blipTableTopRow.append(contributors);
			
			//**************Last edited time**************
			var lastEdited = elementFactory(
				"td",
				{
					"id"		:	BLIP_ID_PREFIX['LAST_EDITED'] + self.blipId,
					"class"		:	"bliplastedited"
				},
				utils.epochToDateTime(self.lastModifiedTime),
				false
			);
			blipTableTopRow.append(lastEdited);
			
			//**************Content/text**************
			var content = elementFactory(
				"td",
				{
					"id"		:	BLIP_ID_PREFIX['CONTENT'] + self.blipId,
					"colspan"	:	"2",
					"class"		:	"blipcontent"
				},
				false,
				false
			);
			blipTableBottomRow.append(content);
			self.renderText(content);
			
			
			
			return blipStructure;
		};
		
		/**
		* Renders a single blip inline
		* @param blip: the blip to render inline
		*/
		self.renderBlipInline = function(inlineBlip) {
		    var parentDivElem = $(document.getElementById(BLIP_ID_PREFIX['INLINE_CONTAINER'] + inlineBlip.blipId));
		    inlineBlip.renderSelfAndAllChildren(parentDivElem, true);
		};
		
		/**
		* Renders all children from this blip and children blips
		* @param parentDivElement: the element to render the first blip to
		* @param isSubReply: indicates the reply should be indented
		*/
		self.renderSelfAndAllChildren = function(parentDivElem, isSubReply) {
			var newParentDivElem = self.render(parentDivElem, isSubReply);
			var children = self.getChildBlips();
			if(children.length > 0) {
			    //We must treat the direct reply differently when rendiering
			    //We must treat inline blips differently when rendering
				for(var i=1; i < children.length; i++) {
				    if(children[i].isInline()) {
				        self.renderBlipInline(children[i]);
				    } else {
				        children[i].renderSelfAndAllChildren(newParentDivElem, true);
			        }
				}
				if(children[0].isInline()) {
				    self.renderBlipInline(children[0]);
				} else {
				    children[0].renderSelfAndAllChildren(newParentDivElem, false);
			    }
			}
			
		}
	};
	
	/**
	* Represent wavelet in javascript way
	* @param rawWavelet: the raw wavelet structure
	* @param rawReadStatus: the raw read status of the blips
	*/
	var Wavelet = function(rawWavelet, rawReadStatus, rawProfiles) {
		//Extract properties
		var self = this;
		self.rawWavelet = rawWavelet;
		self.rootBlipId = rawWavelet['waveletData']['rootBlipId'];
		self.title = rawWavelet['waveletData']['title'];
		self.tags = rawWavelet['waveletData']['tags'];
		self.waveletid = rawWavelet['waveletData']['waveletId'];
		self.waveid = rawWavelet['waveletData']['waveId'];
		self.creator = rawWavelet['waveletData']['creator'];
		self.participants = rawWavelet['waveletData']['participants'];
		self.dataDocuments = rawWavelet['waveletData']['dataDocuments'];
		self.lastModifiedTime = rawWavelet['waveletData']['lastModifiedTime'];
		self.version = rawWavelet['waveletData']['version'];
		self.rawReadStatus = rawReadStatus;
		self.profiles = new Profiles(rawProfiles);
		
		/**
		* Returns the id's of the blips in this wavelet
		* @return array containing blip ids
		*/
		self.getBlipIds = function() {
			var blipIds = [];
			for(k in self.rawWavelet['blips']) {
				blipIds.push(k);	
			}
			return blipIds;
		};
		
		/**
		* Returns a blip object from a blip id
		* @param blipId: the id of the blip to return
		* @return the blip with the provided blip id
		*/
		self.getBlip = function(blipId) {
			var rawBlip = self.rawWavelet['blips'][blipId];
			//Insert the read status to each blip
			var isRead = false;
			for(var i = 0; i < self.rawReadStatus.length; i++) {
				if(self.rawReadStatus[i] === blipId) {
					isRead = true;
					break;	
				}	
			}
			return new Blip(self.profiles, rawBlip, self, isRead);
		};
		
		/**
		* Renders the entire blip structure
		* @param parentDivElem: the parent div element to append the blips to
		*/
		self.renderBlips = function(parentDivElem) {
			self.getBlip(self.rootBlipId).renderSelfAndAllChildren(parentDivElem, false);
		};
		
		/**
		* Renders the participants header
		* @param parentElem: the element to place the participants into
		*/
		self.renderParticipants = function(parentElem) {
			var participants = self.participants;
			for(var i = 0; i < participants.length; i++) {
				var participant = participants[i];
				var profileImage = elementFactory("img",
					{
						"id"		:	PROFILE_ID_PREFIX['IMG'] + participant,
						"src"		:	self.profiles.getImageUrl(participant),
						"alt"		:	utils.getParticipantDisplayNameAndRaw(self.profiles, participant),
						"title"		:	utils.getParticipantDisplayNameAndRaw(self.profiles, participant),
						"height"	:	"40",
						"width"		:	"40"
					},
					false,
					false);
				parentElem.append(profileImage);	
			}
		};
		
		/**
		* Renders the title element
		* @param titleElem: the title element to render to
		*/
		self.renderTitle = function(titleElem) {
		    var title = self.title || "(untitled)";
		    titleElem.text(title);
		    $(document).attr("title", title + utils.getFriendlyUnreadCount() + " - Mr-Ray. Wav-e-mail");
		};
	};
	
	/**
	* Sets up the reply generic error dialog box and its associated actions
	*/
	var setupReplyGenericErrorDialog = function() {
		$("#replysubmitgenericerror").dialog({
			autoOpen: false,
			modal: true,
			autoResize: true,
			width: 'auto',
			buttons: {
				Ok: function() {
					reloadWavelet(undefined);
        			$(this).dialog('close');
        			dialogOpen = false;
				}
			}
		});
	};
    
    /**
    * Sets up the reply error dialog dialog that is shown when Mr-Ray is no long a participant
    */
    var setupReplyNotParticipantErrorDialog = function() {
		$("#replysubmitnotparticipanterror").dialog({
			autoOpen: false,
			modal: true,
			autoResize: true,
			width: 'auto',
			buttons: {
				Ok: function() {
					reloadWavelet(undefined);
        			$(this).dialog('close');
        			dialogOpen = false;
				}
			}
		});
	};
    
	
	/**
	* Sets up all the reply dialog box and its associated actions
	*/
	var setupReplyDialog = function () {
		$('#replyformelement').bind('submit', function() {return false;});
		$("#replyform").attr("style", "visibility:visible;");
		$("#replyform").dialog({
			autoOpen: false,
			modal: true,
			autoResize: true,
			width: 'auto',
			buttons: {
				'Reply': function() {
					//Fetch the variables out of the url
					var blipId = $(clickedButton).attr("id").replace(BLIP_ID_PREFIX['REPLY'], "");
					var reply = $('#response').attr("value");
					var data = {'action': 'REPLY',
        						'blipid': blipId,
        						'reply': reply,
								'waveid': utils.getUrlArg('waveid'),
        						'waveletid': utils.getUrlArg('waveletid'),
        						'email': utils.getUrlArg('email'),
								'auth': utils.getUrlArg('auth')};
					//Change the behaviour if the wave is public
					if(viewerSession.isPublic()) {
					    var name = $('#responderName').attr("value");
					    name = name.replace(/ /g, "_");
					    if (name === "" || /[^\w+$]/.test(name)) {
					        //String is empty or contains banned characters
					        $("#responseNameContainerError").attr("style", "").show();
					        return;
					    }
					    data['name'] = name;
					}
        		    
        			//Sort the gui
        			$("#replyform").dialog('close');
        			$(clickedButton).replaceWith(elementFactory("img",
        			{
        			    "src"   : "http://mr-ray.appspot.com/web/media/workinground.gif"
        			},
        			false, false));
        			
					$.ajax({
        				'dataType': 'json',
        				'url': robotWebAddress + "wave/action/",
        				'type': 'POST',
        				'contentType': 'application/json',
        				'data': JSON.stringify(data),
        				'success': function(data, textStatus) {
        				    $('#working').remove();
        					reloadWavelet(data);
          					$("#replyform").dialog('close');
        				},
        				'error': function(XMLHttpRequest, textStatus, errorThrown) {
        				    $('#working').remove();
                            if(XMLHttpRequest.status === 403) {
                                $('#replysubmitnotparticipanterror').dialog('open');
                            } else {
                                $('#replysubmitgenericerror').dialog('open');
                            }
        				}
      				});
				},
				Cancel: function() {
					$("#replyform").dialog('close');
				}
			},
			close: function() {
				$('#response').attr("value", "");
				$("#responseNameContainerError").hide()
				dialogOpen = false;
			}
		});
	};
	
	/**
	* Sets the page up on first run
	* @param wavelet: the wavelet object you want to render
	*/
	var setup = function(waveletJson) {
	    //Create the objects from the json
        viewerSession = new Session(waveletJson['isPublic'], waveletJson['rwPermission']);
        var wavelet = new Wavelet(waveletJson['wavelet'], waveletJson['readblips'], waveletJson['profiles']);
	    
		//Do these first. They hide some elements. Setting the style on the elements to visible fixes an ie bug
		setupReplyDialog();
        setupReplyGenericErrorDialog();
        setupReplyNotParticipantErrorDialog();
        $('#replyform').attr("style", "");
        $('#replysubmitgenericerror').attr("style", "");
        $('#replysubmitnotparticipanterror').attr("style", "");
        
        //Modify the ui if it is public
        if(viewerSession.isPublic()) {
	        $('#responseNameContainer').attr("style", "").show();
        }
        
        //Render the wavelet
		wavelet.renderBlips($('#blips'));
        wavelet.renderParticipants($('#participants'));
        wavelet.renderTitle($('#headertitle'));
        
	};
	
	/**
	* Reloads the wavelet and re-renders the page.
	* If newWaveletJson is undefined then the existing json is used
	* @param waveletJson: the new waveletJson or undefined to use existing
	*/
	var reloadWavelet = function(newWaveletJson) {
	    if(newWaveletJson !== undefined && newWaveletJson !== null) {
            if(utils.areWaveletsSame(newWaveletJson, waveletJson)) {
                return;
            }
	        waveletJson = newWaveletJson;
        }
        
	    var scrollPosition = $(window).scrollTop();
		$('#headertitle').children().remove();
        $('#participants').children().remove();
        $('#blips').children().remove();
	    
        setup(waveletJson);
        
        $(window).scrollTop(scrollPosition);
	};
	
	/**
	* Refreshes the wave and sets the timeout to do it again
	*/
	reloadPage = function() {
		if(!dialogOpen) {

			var jsondata = JSON.stringify({	'action': 'REFRESH',
     										'waveid': utils.getUrlArg('waveid'),
     										'waveletid': utils.getUrlArg('waveletid'),
     										'email': utils.getUrlArg('email'),
     										'auth': utils.getUrlArg('auth')})
     			
			$.ajax({
     			'dataType': 'json',
     			'url': robotWebAddress + "wave/action/",
     			'type': 'POST',
     			'contentType': 'application/json',
     			'data': jsondata,
     			'success': function(data, textStatus) {
     				reloadWavelet(data);
     			}
   			});
		}
		setTimeout('reloadPage()', 15000);
	};
	
	
	$(document).ready(function() {
	    //Decode some of the variables (these are only sent the page once, only decoded once)
	    robotEmail = Base64.decode(robotEmail);
	    publicEmail = Base64.decode(publicEmail);
	    waveletJson = JSON.parse(Base64.decode(waveletJson));
	    
        setup(waveletJson);
        setTimeout('reloadPage()', 15000);
    });
})(jQuery);