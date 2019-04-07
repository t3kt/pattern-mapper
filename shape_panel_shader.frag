uniform sampler2D sPointPositionalTexture;

in Vertex
{
	vec4 color;
	vec3 worldSpacePos;
	vec2 texCoord0;
	vec2 texCoord1;
	flat int shapeIndex;
} iVert;

out vec4 fragColor;
void main()
{
	TDCheckDiscard();
	
    vec4 color = iVert.color;
    
    vec4 positionalColor = texture(sPointPositionalTexture, iVert.texCoord1);
    
    color = mix(color, positionalColor, positionalColor.a);
    
    TDAlphaTest(color.a);
    fragColor = TDOutputSwizzle(color);
}

