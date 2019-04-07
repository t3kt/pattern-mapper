uniform float uPhaseOffset;
uniform sampler2D sPointPositionalTexture;

in Vertex
{
	vec4 color;
	vec3 worldSpacePos;
	vec2 texCoord0;
	vec2 texCoord1;
	flat int shapeIndex;
	flat vec4 onColor;
	flat vec4 offColor;
	flat float phase;
	flat float count;
} iVert;

out vec4 fragColor;
void main()
{
	TDCheckDiscard();
	
	float phase = iVert.phase + iVert.texCoord0.x;
	phase *= iVert.count;
	phase = mod(phase, 1.0);
    vec4 color = mix(iVert.offColor, iVert.onColor, phase);
    
    vec4 positionalColor = texture(sPointPositionalTexture, iVert.texCoord1);
    
    color = mix(color, positionalColor, positionalColor.a);
    
    TDAlphaTest(color.a);
    fragColor = TDOutputSwizzle(color);
}
